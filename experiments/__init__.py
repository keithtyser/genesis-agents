"""
experiments – small self-contained research micro-experiments
ported to the new sandbox framework.
"""

from __future__ import annotations
import asyncio
from sandbox.world     import WorldState
from sandbox.scheduler import Scheduler
from sandbox.bus       import Bus
from memory            import MemoryStore
from sandbox.memory_manager import MemoryManager
from sandbox.agent     import BaseAgent


# ------------------------------------------------------------------ #
async def run_pair(
    agent_a_cfg: dict,
    agent_b_cfg: dict,
    seed_message: str,
    *,
    max_ticks: int = 60,
    world_path: str | None = None,
) -> Scheduler:
    """
    Spin up two specialised agents and run the scheduler for `max_ticks`.
    Returns the scheduler so the caller can inspect .agents or .world.
    """
    bus   = Bus()
    world = WorldState()                    # fresh scratch world
    store = MemoryStore(path="mem_db")      # shared vector store
    mem   = MemoryManager(world, store)

    a = BaseAgent(bus=bus, mem_mgr=mem, **agent_a_cfg)
    b = BaseAgent(bus=bus, mem_mgr=mem, **agent_b_cfg)

    # push seed into context via a fake system message
    fake_seed = {"role": "user", "name": "Seed", "content": seed_message, "ts": "0"}
    sched = Scheduler(world, [a, b], bus)
    sched.ctx.add(fake_seed)

    await sched.loop(max_ticks=max_ticks)

    if world_path:
        world.save(world_path)
    return sched 