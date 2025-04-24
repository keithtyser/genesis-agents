"""
sandbox.commands – execute simple WORLD: directives inside agent messages.

Supported verbs
---------------
  WORLD: CREATE <kind>
  WORLD: MOVE TO <location>
  WORLD: SET <key>=<value>

BREED directives will be handled by a future BreedingManager (not here).
"""

import re, uuid

_PATTERN = re.compile(r"^WORLD:\s*(.+)", re.IGNORECASE)

def execute(world, content: str):
    """
    Scan *content* for WORLD lines and mutate *world* accordingly.
    Returns list[str] of human-readable event strings (for logging).
    """
    events = []
    for line in content.splitlines():
        m = _PATTERN.match(line.strip())
        if not m:
            continue
        parts = m.group(1).split()
        verb, args = parts[0].upper(), parts[1:]
        if verb == "CREATE" and args:
            kind = args[0]
            oid  = world.add_object(kind, {"creator": "__agent__", "turn": world.tick})
            events.append(f"object {oid} ({kind}) created")
        elif verb == "MOVE" and len(args) >= 2 and args[0].upper() == "TO":
            loc = args[1]
            # location stored per agent later; here just log
            events.append(f"moved to {loc}")
        elif verb == "SET" and args and "=" in args[0]:
            key, value = args[0].split("=", 1)
            events.append(f"set {key}={value}")
        else:
            events.append(f"unknown directive: {verb} {' '.join(args)}")
    return events 