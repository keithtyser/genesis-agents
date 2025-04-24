"""
sandbox.commands – authoritative WORLD: directive handler.

# Verbs & syntax
# --------------
# WORLD: CREATE <kind> [key=value ...]
# WORLD: MOVE TO <location>
# WORLD: SET <key>=<value>
# WORLD: BREED WITH <partner>

# • CREATE           → world.add_object(kind, {...}); returns oid
# • MOVE, SET        → mutate world.agents[speaker]
# • BREED            → publish {"type":"breed_request", "parent":speaker, "partner":partner, "tick":world.tick}

# Function
# --------
#     execute(world, bus, speaker, content) -> list[str]  # events log

Supported verbs
---------------
  WORLD: CREATE <kind>
  WORLD: MOVE TO <location>
  WORLD: SET <key>=<value>

BREED directives will be handled by a future BreedingManager (not here).
"""

from __future__ import annotations
from typing import List, Dict, Any
import re, uuid

_PATTERN = re.compile(r"^WORLD:\s*(.+)", re.IGNORECASE)


def _kv_pairs(tokens: List[str]) -> Dict[str, str]:
    """Return dict for tokens that look like key=value."""
    kv = {}
    for tok in tokens:
        if "=" in tok:
            k, v = tok.split("=", 1)
            kv[k] = v
    return kv


# ------------------------------------------------------------------ #
def execute(world, bus, speaker: str, content: str) -> List[str]:
    """
    Parse *content* line-by-line, mutate `world`, publish on `bus`,
    and return a list of human-readable event strings.
    """
    events: List[str] = []

    for line in content.splitlines():
        m = _PATTERN.match(line.strip())
        if not m:
            continue

        parts     = m.group(1).split()
        verb      = parts[0].upper()
        remainder = parts[1:]

        if verb == "CREATE" and remainder:
            kind, *rest = remainder
            props = _kv_pairs(rest) | {"creator": speaker, "turn": world.tick}
            oid   = world.add_object(kind, props)
            events.append(f"{speaker} created {kind} (id={oid})")

        elif verb == "MOVE" and len(remainder) >= 2 and remainder[0].upper() == "TO":
            loc = remainder[1]
            agent_rec = world.agents.setdefault(speaker, {})
            agent_rec["location"] = loc
            events.append(f"{speaker} moved to {loc}")

        elif verb == "SET" and remainder and "=" in remainder[0]:
            key, value = remainder[0].split("=", 1)
            agent_rec  = world.agents.setdefault(speaker, {})
            agent_rec[key] = value
            events.append(f"{speaker} set {key}={value}")

        elif verb == "BREED" and len(remainder) >= 2 and remainder[0].upper() == "WITH":
            partner = remainder[1]
            payload = {
                "type":    "breed_request",
                "parent":  speaker,
                "partner": partner,
                "tick":    world.tick,
            }
            pub = bus.publish("breed_request", payload)
            # support both sync & async Bus, but avoid task creation if no event loop
            import asyncio, inspect
            if inspect.isawaitable(pub):
                try:
                    loop = asyncio.get_running_loop()
                    asyncio.create_task(pub)  # fire-and-forget only if loop exists
                except RuntimeError:
                    pass  # no event loop, skip task creation
            events.append(f"{speaker} asked to breed with {partner}")

        else:
            events.append(f"{speaker} issued unknown directive: {verb}")

    return events 