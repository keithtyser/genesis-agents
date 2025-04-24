from __future__ import annotations
import asyncio, datetime as dt
from typing import List, Dict, Any, Optional

from sandbox import llm

# tiny alias type for clarity
Message = Dict[str, Any]


class BaseAgent:
    """A reusable assistant agent."""

    # -------------------------------------------------- #
    def __init__(
        self,
        name: str,
        system_msg: str,
        temperature: float = 0.8,
        *,
        bus=None,                # will be Bus instance after Task 1
        mem_mgr=None,            # MemoryManager after Task 6
    ):
        self.name = name
        self.system_msg = system_msg
        self.temperature = temperature
        self.bus = bus
        self.mem_mgr = mem_mgr

        self._last_prompt: List[Message] | None = None
        self._last_reply: str | None = None

    # -------------------------------------------------- #
    async def think(
        self,
        world,                        # WILL be WorldState – unused for now
        recent: List[Message],
    ) -> Message:
        """
        Produce one assistant reply based on recent conversation.

        Parameters
        ----------
        world   – placeholder; gives access to locations/resources in future
        recent  – list of the most recent chat messages (dicts with role/name/content)

        Returns
        -------
        Message dict ready to drop into chat history.
        """

        # 1. optional memory recall (Task 6 will fill this)
        mem_block = ""
        if self.mem_mgr:
            recalls = self.mem_mgr.recall(self.name, recent[-1]["content"] if recent else "")
            if recalls:
                bullets = "\n".join("• " + r for r in recalls)
                mem_block = "[Memory recall]\n" + bullets

        # 2. build prompt
        prompt: List[Message] = [{"role": "system", "content": self.system_msg}]
        if mem_block:
            prompt.append({"role": "system", "name": "Memory", "content": mem_block})
        prompt.extend(recent)

        self._last_prompt = prompt  # stash for debug

        # 3. call LLM
        reply_text = await llm.chat(
            prompt,
            temperature=self.temperature,
            max_tokens=256,
        )

        self._last_reply = reply_text

        # 4. craft message
        msg: Message = {
            "role": "assistant",
            "name": self.name,
            "content": reply_text,
            "ts": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }

        # 5. persist to memory store (noop until Task 6)
        if self.mem_mgr:
            self.mem_mgr.store(self.name, reply_text)

        # 6. publish to bus if present
        if self.bus:
            # non-blocking; if bus.publish is async, await it
            pub = self.bus.publish("chat", msg)
            if asyncio.iscoroutine(pub):
                await pub

        return msg

    # -------------------------------------------------- #
    # Simple helpers for manual inspection
    # -------------------------------------------------- #
    @property
    def last_prompt(self) -> Optional[List[Message]]:
        return self._last_prompt

    @property
    def last_reply(self) -> Optional[str]:
        return self._last_reply 