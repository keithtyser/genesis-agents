"""
sandbox.llm – Async OpenAI helper with global rate-limit + retry.

Public function
---------------
    async chat(messages: list[dict], *, model: str|None = None, **kwargs) -> str
        Returns **content** string of first choice.

Environment variables
---------------------
    OPENAI_API_KEY            mandatory
    OPENAI_MODEL              default model (fallback 'gpt-4o-mini')
    OPENAI_PARALLEL_MAX       max concurrent calls (default 5)
    MAX_PROMPT_TOKENS         max tokens in prompt (default 12000)
"""

from __future__ import annotations
import os, asyncio, typing as _t
from tenacity import retry, wait_random_exponential, stop_after_attempt, RetryError
from openai import AsyncOpenAI, OpenAIError
import contextvars
import tiktoken

# -------------------------------------------------------------- #
# Global semaphore – one per interpreter
_MAX = int(os.getenv("OPENAI_PARALLEL_MAX", "5"))

# maps event-loop id -> semaphore
_loop_sem: contextvars.ContextVar[asyncio.Semaphore] = contextvars.ContextVar("loop_sem")

def _get_semaphore() -> asyncio.Semaphore:
    """Return a semaphore bound to the *current* running loop."""
    try:
        sem = _loop_sem.get()
    except LookupError:
        sem = asyncio.Semaphore(int(os.getenv("OPENAI_PARALLEL_MAX", "5")))
        _loop_sem.set(sem)
    return sem

# Lazy singleton client (avoids import-time KEY check)
_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI()  # picks up key from env var
    return _client


# -------------------------------------------------------------- #
class LLMError(RuntimeError):
    """Raised after all retries fail."""


# -------------------------------------------------------------- #
@retry(                      # ≤4 total attempts
    wait=wait_random_exponential(min=2, max=20),
    stop=stop_after_attempt(4),
    reraise=True,
)
async def _chat_once(
    messages: list[dict[str, str]],
    *,
    model: str,
    **kwargs,
) -> str:
    """
    Single OpenAI call wrapped by tenacity. Returns content string.
    """
    async with _get_semaphore():
        client = _get_client()
        try:
            resp = await client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs,
            )
            return resp.choices[0].message.content.strip()
        except OpenAIError as e:
            # network / rate errors will be retried by tenacity
            print(f"[llm] OpenAIError → will retry: {e}")
            raise


# -------------------------------------------------------------- #
MAX_PROMPT_TOKENS = int(os.getenv("MAX_PROMPT_TOKENS", "12000"))

def _num_tokens(messages, model="gpt-4o-mini"):
    model = model or "gpt-4o-mini"
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    n = 0
    for m in messages:
        n += 4                       # role + name etc.
        n += len(enc.encode(m["content"]))
    return n


# -------------------------------------------------------------- #
async def chat(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float = 0.7,
    **kwargs,
) -> str:
    """
    High-level helper with retry and global concurrency limit.
    Raises LLMError if all retries fail.
    """
    if not messages:
        raise ValueError("messages list cannot be empty")

    _model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    tokens = _num_tokens(messages, model=_model)
    if tokens > MAX_PROMPT_TOKENS:
        # keep system msg + last 100 msgs until under limit
        sys_msg = messages[0]
        tail    = messages[-100:]
        while _num_tokens([sys_msg] + tail, model=_model) > MAX_PROMPT_TOKENS:
            tail.pop(0)          # drop oldest one at a time
        messages = [sys_msg] + tail

    try:
        return await _chat_once(messages, model=_model, temperature=temperature, **kwargs)
    except RetryError as final:
        raise LLMError(
            f"OpenAI chat failed after {final.last_attempt.attempt_number} attempts"
        ) from final
    except Exception as e:
        # crude local summary of the last user/assistant pair
        raw = ""
        for msg in reversed(messages):
            if msg.get("content"):
                raw = msg["content"]
                break
        fallback = raw[-500:] if raw else "No relevant conversation content found."
        return f"[LLM error: {e.__class__.__name__}] {fallback}" 