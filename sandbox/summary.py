# Async bullet-point summariser used by ContextManager.
from __future__ import annotations
from typing import List
import os
from sandbox.llm import chat
from sandbox.config import SUMMARISE_MODEL

async def summarise(messages: List[dict]) -> str:
    """
    Compress `messages` (list of dicts with 'name' & 'content')
    into ≤10 bullets, quoting any WORLD: lines verbatim.
    """
    if not messages:
        return ""

    # Flatten slice into plain text
    transcript = "\n".join(
        f"{m.get('name','?')}: {m.get('content','')}" for m in messages
    )

    prompt = [
        {
            "role": "user",
            "content": (
                "Summarise the following conversation into ten or fewer concise bullets. "
                "If any line begins with 'WORLD:' quote that directive verbatim.\n\n"
                + transcript[:4000]
            ),
        }
    ]

    try:
        return await chat(prompt, model=SUMMARISE_MODEL, temperature=0)
    except Exception:
        # naive fallback = first 3 lines
        plain = transcript.splitlines()[:3]
        return " / ".join(plain)[:400]

async def summarise(transcript: str, model: str | None = None) -> str:
    prompt = _make_prompt(transcript)
    try:
        return await chat(prompt, model=SUMMARISE_MODEL, temperature=0)
    except Exception:
        # naive fallback = first 3 lines
        plain = transcript.splitlines()[:3]
        return " / ".join(plain)[:400] 