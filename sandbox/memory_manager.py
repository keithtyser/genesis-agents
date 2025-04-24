from __future__ import annotations
from typing import List
from memory import MemoryStore


class MemoryManager:
    def __init__(self, world, store: MemoryStore, k: int = 3):
        self.world = world
        self.memory_store = store
        self.k     = k                # top-k to return

    # -------------------------------------------------- #
    # public helpers called by agents / scheduler
    # -------------------------------------------------- #
    async def store(self, agent: str, text: str) -> None:
        """Deduplicate + summarise + embed."""
        await self.memory_store.summarise_and_add(agent, text)

    def recall(self, agent: str, last_msg: str) -> List[str]:
        """
        Return ≤ k snippets relevant for *agent*.
        Query is built from the agent's last visible message
        plus their current location (if any in world.agents).
        """
        loc = self.world.agents.get(agent, {}).get("location", "")
        query = f"{last_msg} {loc}".strip() or agent
        return self.memory_store.recall(agent, query, k=self.k) 