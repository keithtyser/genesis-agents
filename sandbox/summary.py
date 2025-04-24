# Async bullet-point summariser used by ContextManager.
from __future__ import annotations
from typing import List
import os
from sandbox import llm
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

    return await llm.chat(prompt, model=SUMMARISE_MODEL, temperature=0) 