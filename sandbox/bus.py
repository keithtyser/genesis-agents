"""
sandbox.bus – lightweight pub-sub message bus for asyncio tasks.
"""

from __future__ import annotations
import asyncio, uuid, datetime as dt
from dataclasses import dataclass, field
from typing import Dict, List


# -------------------------------------------------- #
@dataclass(frozen=True)
class Message:
    """Immutable envelope for all chat / world traffic."""
    sender:  str
    content: str
    topic:   str = "chat"          # default channel
    id:      str = field(default_factory=lambda: uuid.uuid4().hex, init=False)
    ts:      str = field(
        default_factory=lambda: dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        init=False,
    )


# -------------------------------------------------- #
class Bus:
    """Async pub-sub hub (in-proc, no persistence)."""

    def __init__(self):
        # topic -> list[Queue]
        self._subs: Dict[str, List[asyncio.Queue]] = {}

    # ------------------------------ #
    def subscribe(self, topic: str = "chat", *, maxsize: int | None = None) -> asyncio.Queue:
        """
        Returns an asyncio.Queue that will receive every future Message on *topic*.
        Caller must `await queue.get()` to pop messages.
        """
        # Convert None to 0 for unlimited size
        queue_maxsize = maxsize if maxsize is not None else 0
        q: asyncio.Queue = asyncio.Queue(maxsize=queue_maxsize)
        self._subs.setdefault(topic, []).append(q)
        return q

    # ------------------------------ #
    async def publish(self, topic: str, msg: Message | str, sender: str = ""):
        """
        Publish Message (or plain string) on *topic*.
        Sender may be supplied if msg is str.
        """
        if isinstance(msg, str):
            msg = Message(sender=sender, content=msg, topic=topic)

        for q in self._subs.get(topic, []):
            # wait if queue full
            await q.put(msg) 