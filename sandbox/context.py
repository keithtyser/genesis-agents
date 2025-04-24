# Rolling-summary context manager.
#
# Typical usage
# -------------
# ctx = ContextManager(world)
# ctx.add(msg_dict)
# prompt = ctx.build_prompt(system_msg=<str>,
#                           memory_block=<str|"">)

from __future__ import annotations
import collections
from typing import List, Dict, Any, Deque, Optional
from sandbox.config import MAX_VISIBLE_TURNS, SUMMARY_HORIZON
from sandbox.summary import summarise

Message = Dict[str, Any]   # alias for clarity


class ContextManager:
    def __init__(self, world):
        self.world = world
        self._recent: Deque[Message] = collections.deque()
        self._summary: Optional[str] = None
        self._since_rollup = 0

    # -------------------------------------------------- #
    def add(self, msg: Message) -> None:
        """Append newest chat message and count toward roll-up horizon."""
        self._recent.append(msg)
        self._since_rollup += 1
        # → NO trimming here; we need the older slice intact for roll-up

    # -------------------------------------------------- #
    async def rollup(self):
        """
        If we have at least SUMMARY_HORIZON new messages OR the deque is
        already bigger than MAX_VISIBLE_TURNS, summarise everything **except**
        the last MAX_VISIBLE_TURNS into a single bullet block.
        """
        if len(self._recent) <= MAX_VISIBLE_TURNS:
            self._since_rollup = 0
            return

        if self._since_rollup < SUMMARY_HORIZON:
            # not yet time to roll up
            return

        older = list(self._recent)[:-MAX_VISIBLE_TURNS]
        self._summary = await summarise(older)

        # keep only the fresh tail
        tail = list(self._recent)[-MAX_VISIBLE_TURNS:]
        self._recent.clear()
        self._recent.extend(tail)

        self._since_rollup = 0

    # -------------------------------------------------- #
    def build_prompt(
        self,
        *,
        system_msg: str,
        memory_block: str = "",
    ) -> List[Message]:
        """
        Returns list[dict] ready for llm.chat().

        Layout:
        1. system message
        2. optional memory block (as system Memory)
        3. optional running summary
        4. recent raw messages (<= MAX_VISIBLE_TURNS)
        """
        prompt: List[Message] = [{"role": "system", "content": system_msg}]

        if memory_block:
            prompt.append(
                {"role": "system", "name": "Memory", "content": memory_block}
            )
        if self._summary:
            prompt.append(
                {"role": "system", "name": "Summary", "content": self._summary}
            )

        prompt.extend(self._recent)
        return prompt

    # -------------------------------------------------- #
    @property
    def summary(self) -> Optional[str]:
        return self._summary

    @property
    def recent_messages(self) -> List[Message]:
        return list(self._recent) 