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
"""

from __future__ import annotations
import os, asyncio, typing as _t
from tenacity import retry, wait_random_exponential, stop_after_attempt, RetryError
from openai import AsyncOpenAI, OpenAIError
import contextvars

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
async def chat(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    **kwargs,
) -> str:
    """
    High-level helper with retry and global concurrency limit.
    Raises LLMError if all retries fail.
    """
    if not messages:
        raise ValueError("messages list cannot be empty")

    _model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    try:
        return await _chat_once(messages, model=_model, **kwargs)
    except RetryError as final:
        raise LLMError(
            f"OpenAI chat failed after {final.last_attempt.attempt_number} attempts"
        ) from final 