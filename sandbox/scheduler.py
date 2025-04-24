"""
sandbox.scheduler – drives the simulation tick-by-tick.

Typical usage
-------------
sched = Scheduler(world, agents, bus)
await sched.loop(max_ticks=1000)
"""

from __future__ import annotations
import asyncio, itertools, os, datetime as dt
from typing import List
from sandbox.context        import ContextManager
from sandbox.commands       import execute as exec_cmds
from sandbox.world          import WorldState
from sandbox.bus            import Bus
from sandbox.breeding import BreedingManager

class Scheduler:
    def __init__(
        self,
        world: WorldState,
        agents: List,
        bus: Bus,
    ):
        self.world  = world
        self.agents = agents
        self.bus    = bus

        self.ctx = ContextManager(world)
        self.breeder = BreedingManager(world, bus, self)
        self._cursor = itertools.cycle(self.agents)

    # -------------------------------------------------- #
    async def run_tick(self):
        agent = next(self._cursor)

        # ❶ Agent thinks
        msg = await agent.think(self.world, self.ctx)

        # ❷ Add to context
        self.ctx.add(msg)
        await self.ctx.rollup()

        # ❸ Execute WORLD commands (if any) – mutates world
        events = exec_cmds(self.world, self.bus, msg["name"], msg["content"])
        if events:
            for ev in events:
                print(f"[world] {ev}")

        # ❹ Bump tick & maybe persist
        self.world.tick += 1
        if self.world.tick % 10 == 0:
            self.world.save("world.json")
            print(f"[{dt.datetime.now().strftime('%H:%M:%S')}] tick={self.world.tick} saved.")
        await self.breeder.step()
        # Check if new agents were added and refresh cursor to include them immediately after current agent
        import itertools
        self._cursor = itertools.cycle(self.agents)
        # Move cursor to the agent after the current one to ensure new agents are included soon
        for _ in range(self.agents.index(agent) + 1):
            next(self._cursor)

    # -------------------------------------------------- #
    async def loop(self, max_ticks: int | None = None):
        count = 0
        while True:
            await self.run_tick()
            count += 1
            if max_ticks and count >= max_ticks:
                break

from memory                 import MemoryStore
from sandbox.memory_manager import MemoryManager
from sandbox.agent          import BaseAgent

async def build_default_scheduler():
    """
    Utility that spins up a minimal sandbox with Alice & Bob
    and returns Scheduler instance ready to run.
    """
    bus    = Bus()
    world  = WorldState.load("world.json")
    store  = MemoryStore(path="mem_db")
    memmgr = MemoryManager(world, store)

    alice = BaseAgent("Alice", "You are Alice, an optimistic explorer.",
                      bus=bus, mem_mgr=memmgr)
    bob   = BaseAgent("Bob",   "You are Bob, a pragmatic builder.",
                      bus=bus, mem_mgr=memmgr)

    # register subscribers if you want to inspect bus; not needed for now
    return Scheduler(world, [alice, bob], bus)

# ------------------------------------------------------------------ #
def build_default(world: WorldState):
    """
    Convenience factory used by CLI.
    Builds a Bus, MemoryManager, two starter agents, and returns Scheduler.
    """
    from sandbox.bus             import Bus
    from memory                  import MemoryStore
    from sandbox.memory_manager  import MemoryManager
    from sandbox.agent           import BaseAgent

    bus   = Bus()
    store = MemoryStore(path="mem_db")
    mem   = MemoryManager(world, store)

    alice = BaseAgent("Alice", "You are Alice, a curious explorer.", bus=bus, mem_mgr=mem)
    bob   = BaseAgent("Bob",   "You are Bob, a pragmatic builder.",  bus=bus, mem_mgr=mem)

    return Scheduler(world, [alice, bob], bus) 