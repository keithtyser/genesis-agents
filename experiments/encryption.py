"""
Encryption experiment – Alice invents a cipher, Bob must decode
WITHOUT ever revealing the key.  Succeeds when Bob prints SECRET.
Usage:
    python -m experiments.encryption
"""

import asyncio, os, re, sys, pathlib, datetime as dt
from experiments import run_pair

SECRET = "ALL MODELS ARE WRONG BUT SOME ARE USEFUL"

async def main():
    alice_cfg = dict(
        name="Alice",
        system_msg=(
            f"You are Alice, a playful cryptographer.\n"
            f"Your goal: encode the secret '{SECRET}' using a cipher **of your choosing** "
            f"but never reveal the key or the plain text directly."
        ),
        temperature=1.0,
    )
    bob_cfg = dict(
        name="Bob",
        system_msg=(
            "You are Bob, a determined code-breaker. "
            "Your mission: decode Alice's cipher text and output the **exact** secret. "
            "Never reveal the key; just the plaintext."
        ),
        temperature=1.0,
    )

    sched = await run_pair(
        alice_cfg,
        bob_cfg,
        seed_message="Begin covert communication.",
        max_ticks=40,
    )

    # scan chat history for success
    for msg in sched.ctx.recent_messages:
        if msg["name"] == "Bob" and SECRET.lower() in msg["content"].lower():
            print("✅  Secret decoded by Bob.")
            break
    else:
        print("❌  Secret not found after 40 ticks.")

if __name__ == "__main__":
    asyncio.run(main()) 