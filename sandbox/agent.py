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
        bus=None,                # sandbox.bus.Bus | None
        mem_mgr=None,            # sandbox.memory_manager.MemoryManager | None
    ):
        self.name         = name
        self.system_msg   = system_msg
        self.temperature  = temperature

        self.bus     = bus
        self.mem_mgr = mem_mgr

        # debug introspection
        self._last_prompt: Optional[List[Message]] = None
        self._last_reply:  Optional[str]           = None

    # -------------------------------------------------- #
    async def think(
        self,
        world,                       # sandbox.world.WorldState
        context_mgr,                 # sandbox.context.ContextManager
    ) -> Message:
        """
        Produce one assistant message.

        Returns
        -------
        dict with keys: role, name, content, ts
        """
        # 1) MEMORY RECALL BLOCK
        mem_block = ""
        if self.mem_mgr:
            last_raw = context_mgr.recent_messages[-1]["content"] if context_mgr.recent_messages else ""
            recalls  = self.mem_mgr.recall(self.name, last_raw)
            if recalls:
                bullets   = "\n".join("• " + r for r in recalls)
                mem_block = "[Memory recall]\n" + bullets

        # 2) BUILD PROMPT (ContextManager inserts summary + recents)
        prompt = context_mgr.build_prompt(
            system_msg=self.system_msg,
            memory_block=mem_block,
        )
        self._last_prompt = prompt

        # 3) CALL LLM
        reply_text = await llm.chat(
            prompt,
            temperature=self.temperature,
            max_tokens=256,
        )
        self._last_reply = reply_text

        # 4) FORM MESSAGE OBJECT
        msg: Message = {
            "role":    "assistant",
            "name":    self.name,
            "content": reply_text,
            "ts":      dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }

        # 5) PERSIST TO MEMORY
        if self.mem_mgr:
            await self.mem_mgr.store(self.name, reply_text)

        # 6) PUBLISH ON BUS
        if self.bus:
            pub = self.bus.publish("chat", msg)
            if asyncio.iscoroutine(pub):
                await pub  # handle async bus

        return msg

    # -------------------------------------------------- #
    # Debug helpers
    # -------------------------------------------------- #
    @property
    def last_prompt(self) -> Optional[List[Message]]:
        return self._last_prompt

    @property
    def last_reply(self) -> Optional[str]:
        return self._last_reply 