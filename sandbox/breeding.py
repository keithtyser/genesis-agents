"""
sandbox.breeding – listens for reciprocal BREED requests and spawns child agents.

Rules
-----
• A parent issues {"type":"breed_request","parent":P,"partner":Q,"tick":t}
• If Q issues the symmetric request in *the same tick t*, spawn exactly one child
• Child name format:  child_<tick>_<P[:3]>_<Q[:3]>_<4hex>
• Child system_msg combines parent traits; temperature = avg(parent temps)

Public API
----------
    class BreedingManager
        .step()          ← call once per scheduler tick
"""

from __future__ import annotations
import asyncio, uuid, re
from typing import Dict, Tuple, Set, List
from sandbox.agent import BaseAgent

class BreedingManager:
    def __init__(self, world, bus, scheduler):
        self.world      = world
        self.bus        = bus
        self.scheduler  = scheduler            # need to append new agents
        self.queue      = bus.subscribe("breed_request")
        # pending[(P,Q)] = tick
        self.pending: Dict[Tuple[str, str], int] = {}
        self.spawned_pairs: Set[Tuple[str, str]] = set()

    # -------------------------------------------------- #
    async def step(self):
        """
        Drain queue non-blocking; evaluate mutual requests for current tick.
        """
        drained: List[Dict] = []
        while True:
            try:
                drained.append(self.queue.get_nowait())
            except asyncio.QueueEmpty:
                break

        for evt in drained:
            p, q, t = evt["parent"], evt["partner"], evt["tick"]
            key     = tuple(sorted((p, q)))
            if key in self.spawned_pairs:   # already produced
                continue
            self.pending[(p, q)] = t
            print(f"[breeding-debug] Received request: {p} wants to breed with {q} at tick {t}")

        # look for reciprocal pairs (P,Q) & (Q,P) with same or adjacent tick
        for (p, q), t1 in list(self.pending.items()):
            reciprocal = (q, p)
            if reciprocal in self.pending:
                t2 = self.pending[reciprocal]
                print(f"[breeding-debug] Checking match: {p}-{q} at tick {t1} vs {q}-{p} at tick {t2}")
                # allow if ticks are equal OR adjacent
                if abs(t1 - t2) <= 1:
                    self._spawn_child(p, q, max(t1, t2))
                    for k in ((p, q), reciprocal):
                        self.pending.pop(k, None)
                    self.spawned_pairs.add(tuple(sorted((p, q))))

    # -------------------------------------------------- #
    def _spawn_child(self, p: str, q: str, tick: int):
        """
        Create child agent; add to scheduler & world; announce to bus.
        """
        uid   = uuid.uuid4().hex[:4]
        name  = f"child_{tick}_{p[:3]}_{q[:3]}_{uid}"

        # helper: find parent agents in scheduler list
        def _find_temp(parent):
            for ag in self.scheduler.agents:
                if ag.name == parent:
                    return ag.temperature
            return 0.8

        temp = round(max(0.1, min(1.0, (_find_temp(p)+_find_temp(q))/2)), 2)

        # combine traits by regexing for adjectives after "You are X, ..."
        def _trait(agent_name) -> str:
            for ag in self.scheduler.agents:
                if ag.name == agent_name:
                    m = re.search(r"You are .*?,\s*(.+?)[\.,]", ag.system_msg)
                    return m.group(1) if m else "curious"
            return "curious"

        sys_msg = (
            f"You are {name}, child of {p} ({_trait(p)}) and {q} ({_trait(q)}). "
            f"You strive to balance the traits of your parents."
        )

        child = BaseAgent(
            name,
            sys_msg,
            temperature=temp,
            bus=self.bus,
            mem_mgr=getattr(self.scheduler.agents[0], 'mem_mgr', None)  # reuse same mem_mgr
        )

        # inject into scheduler rotation immediately AFTER current agent list
        self.scheduler.agents.append(child)
        # refresh round-robin cycle
        import itertools
        self.scheduler._cursor = itertools.cycle(self.scheduler.agents)

        # update world
        self.world.agents[name] = {
            "parents": [p, q],
            "born":    tick,
            "temperature": temp,
        }
        # Save world state immediately after adding child
        self.world.save("world.json")
        print(f"[breeding-debug] World state saved with new child {name}")

        print(f"[breeding] 🍼  Spawned {name} (T={temp}) from {p}+{q}") 