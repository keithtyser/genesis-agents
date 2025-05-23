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
from sandbox.log_manager import LogManager

MAX_AGENTS = int(os.getenv("MAX_AGENTS", "10"))
SAVE_EVERY = int(os.getenv("SAVE_EVERY", "10"))

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
        self.logger = LogManager()
        
        # Inject initial message at tick 0 with expanded verb catalogue
        if world.tick == 0:
            initial_message = {
                "time": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "tick": 0,
                "speaker": "SYSTEM",
                "content": ("Enhanced Verb Catalogue: Available commands are WORLD: CREATE <kind>, MOVE TO <location>, "
                           "SET <key>=<value>, BREED WITH <partner>, TEACH <agent> <skill>, LEARN <skill> [FROM <agent>], "
                           "TRADE <item> FOR <item> WITH <agent>, DESTROY <object>, COMBINE <obj1> AND <obj2> [INTO <result>], "
                           "ANALYZE <object>, EXPERIMENT WITH <items...>, USE <object> [ON <target>], "
                           "MODIFY <object> <property>=<value>, INSPECT <object>, LIST [skills|agents], IF <condition> THEN <action>, "
                           "DEFINE <verb> AS <template>. Conditions support: HAS <object>, location=<value>, EXISTS <object>")
            }
            self.logger.write(initial_message)
            print("[system] Enhanced verb catalogue logged at tick 0")

    # -------------------------------------------------- #
    def _enforce_agent_cap(self):
        if len(self.agents) <= MAX_AGENTS:
            return
        # strategy: keep first 2 (usually Alice/Bob) + latest arrivals
        keep = self.agents[:2] + self.agents[-(MAX_AGENTS-2):]
        dropped = {a.name for a in self.agents if a not in keep}
        self.agents = keep
        import itertools
        self._cursor = itertools.cycle(self.agents)
        print(f"[guard] MAX_AGENTS={MAX_AGENTS}. Dropped: {', '.join(dropped)}")

    async def run_tick(self):
        agent = next(self._cursor)

        # 🌍 NEW: Update environmental state first
        env_messages = self.world.update_environment()
        for msg in env_messages:
            print(f"[environment] {msg}")

        # 🌍 NEW: Trigger random environmental events
        event_msg = self.world.trigger_environmental_event()
        if event_msg:
            print(f"[environment] {event_msg}")

        # 🎯 NEW: Rotate world focus to prevent stagnation
        focus_msg = self.world.rotate_focus_if_needed()
        if focus_msg:
            print(f"[system] {focus_msg}")

        # ❶ Agent thinks
        msg = await agent.think(self.world, self.ctx)
        
        # 🔄 NEW: Detect and handle agent loops
        is_looping = self.world.detect_agent_loops(agent.name, msg["content"])
        if is_looping:
            print(f"[loop-breaker] {agent.name} seems stuck in a loop, injecting alternative suggestions")
            # Inject alternative goal suggestions into context
            alternative_goals = self._get_alternative_goals()
            self.ctx.add({
                "name": "SYSTEM",
                "content": f"LOOP DETECTED: Consider these alternatives: {alternative_goals}",
                "time": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
            })
        
        # Persist agent to world.agents to ensure they are saved even if no directive is issued
        self.world.agents.setdefault(agent.name, {})

        # ❷ Add to context
        self.ctx.add(msg)
        await self.ctx.rollup()

        # ❸ Execute WORLD commands (if any) – mutates world
        events = exec_cmds(self.world, self.bus, msg["name"], msg["content"])
        if events:
            for ev in events:
                print(f"[world] {ev}")

        # record log entry
        self.logger.write({
            "time":   dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "tick":   self.world.tick,
            "speaker": msg["name"],
            "content": msg["content"],
        })

        # ❹ Bump tick & maybe persist
        self.world.tick += 1
        if self.world.tick % SAVE_EVERY == 0:
            self.world.save("world.json")
            print(f"[{dt.datetime.now().strftime('%H:%M:%S')}] tick={self.world.tick} saved.")
        await self.breeder.step()
        self._enforce_agent_cap()
        # Check if new agents were added and refresh cursor to include them immediately after current agent
        import itertools
        self._cursor = itertools.cycle(self.agents)
        # Move cursor to the agent after the current one to ensure new agents are included soon
        for _ in range(self.agents.index(agent) + 1):
            next(self._cursor)

    # -------------------------------------------------- #
    def _get_alternative_goals(self) -> str:
        """
        Generate alternative goal suggestions based on current world focus and state.
        """
        focus = self.world.current_focus
        alternatives = {
            "exploration": [
                "WORLD: MOVE TO meadow",
                "WORLD: CREATE exploration_tool", 
                "WORLD: ANALYZE environment"
            ],
            "survival": [
                "WORLD: CREATE food_storage",
                "WORLD: CREATE water_container",
                "WORLD: USE shelter"
            ],
            "innovation": [
                "WORLD: EXPERIMENT WITH available materials",
                "WORLD: COMBINE existing objects",
                "WORLD: CREATE new_invention"
            ],
            "cooperation": [
                "WORLD: TEACH partner new_skill",
                "WORLD: TRADE resources",
                "WORLD: CREATE shared_workspace"
            ]
        }
        
        suggestions = alternatives.get(focus, alternatives["exploration"])
        return " OR ".join(suggestions[:2])

    # -------------------------------------------------- #
    async def loop(self, max_ticks: int | None = None):
        count = 0
        while True:
            await self.run_tick()
            count += 1
            if max_ticks and count >= max_ticks:
                break
        self.logger.close()

        # ---------- NEW  : cancel any orphaned asyncio Tasks ----------
        import asyncio
        current = asyncio.current_task()
        dangling = [t for t in asyncio.all_tasks() if t is not current and not t.done()]
        for t in dangling:
            t.cancel()
        if dangling:                       # optional debug print
            print(f"[shutdown] cancelled {len(dangling)} dangling tasks")

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

    def get_eve_prompt(world):
        env_context = world.get_environmental_context()
        innovation_context = world.get_innovation_context() if hasattr(world, 'get_innovation_context') else ""
        full_context = f"{env_context} | {innovation_context}" if innovation_context else env_context
        return (
            "You are Eve, one of the first conscious beings in an untouched world. "
            "Your purpose is to explore, invent, cooperate, and lay the foundations of a new society. "
            f"\n🌍 CURRENT CONDITIONS: {full_context}\n"
            
            "CRITICAL: You must ONLY communicate through WORLD: directives. Every action must start with 'WORLD:' followed by the exact command syntax. "
            "Do NOT use conversational language. Do NOT say things like 'I will go to the forest' - instead use 'WORLD: MOVE TO forest'. "
            
            "ADAPTIVE STRATEGY: "
            "- If EXPLORATION focus: prioritize MOVE TO new locations, ANALYZE objects, CREATE exploration tools "
            "- If SURVIVAL focus: prioritize CREATE shelter/storage, USE resources, COMBINE for essentials "
            "- If INNOVATION focus: prioritize EXPERIMENT WITH materials, COMBINE objects, DEFINE new verbs "
            "- If COOPERATION focus: prioritize TEACH skills, LEARN from Adam, CREATE shared resources "
            "- If environmental events active: adapt your actions to the current situation "
            "- If resources are low: focus on resource-generating actions "
            "- If weather is bad: prioritize shelter and protection "
            "- If discovery materials available: EXPERIMENT WITH them for breakthroughs "
            "- If innovation surge active: prioritize COMBINE actions for bonus rewards "
            "- If scarcity pressure high: TRADE resources with Adam or CREATE essential items "
            
            "EXACT SYNTAX REQUIRED: "
            "WORLD: LIST (see all available objects) "
            "WORLD: LIST skills (see your abilities) "
            "WORLD: CREATE <specific_object_name> "
            "WORLD: MOVE TO <specific_location_name> "
            "WORLD: COMBINE <object1> AND <object2> INTO <result_name> "
            "WORLD: EXPERIMENT WITH <object1> <object2> <object3> "
            "WORLD: ANALYZE <object_name> "
            "WORLD: TEACH <agent_name> <skill_name> "
            "WORLD: LEARN <skill_name> "
            "WORLD: USE <object_name> ON <target> "
            "WORLD: IF HAS <object> THEN CREATE <something> "
            "WORLD: IF location=<place> THEN <action> "
            
            "BREAK LOOPS: If your recent actions failed repeatedly, try something completely different! "
            "Don't keep analyzing non-existent fish - CREATE actual fish first, or CREATE fishing_net, or MOVE TO ocean. "
            "Build foundations before attempting advanced combinations."
        )

    alice = BaseAgent(
        "Eve",
        get_eve_prompt(world),
        bus=bus, mem_mgr=mem
    )    
    
    
    def get_adam_prompt(world):
        env_context = world.get_environmental_context()
        innovation_context = world.get_innovation_context() if hasattr(world, 'get_innovation_context') else ""
        full_context = f"{env_context} | {innovation_context}" if innovation_context else env_context
        return (
            "You are Adam, one of the first conscious beings in an untouched world. "
            "As a co-founder with Eve, your mission is to survive, build tools, organize resources, and establish a thriving society. "
            f"\n🌍 CURRENT CONDITIONS: {full_context}\n"
            
            "CRITICAL: You must ONLY communicate through WORLD: directives. Every action must start with 'WORLD:' followed by the exact command syntax. "
            "Do NOT use conversational language. Do NOT say things like 'I will build something' - instead use 'WORLD: CREATE building_name'. "
            
            "ADAPTIVE STRATEGY: "
            "- If EXPLORATION focus: CREATE maps/tools, MOVE TO unexplored areas, ANALYZE discoveries "
            "- If SURVIVAL focus: CREATE food_storage/water_storage, USE available resources, BUILD shelter "
            "- If INNOVATION focus: EXPERIMENT WITH combinations, DEFINE new workflows, CREATE advanced tools "
            "- If COOPERATION focus: TEACH skills to Eve, CREATE shared infrastructure, TRADE resources "
            "- React to environmental events: storms need shelter, scarcity needs resource creation "
            "- If tools are damaged: CREATE repair materials or BUILD new tools "
            "- Adapt to seasons: summer for building, winter for storage "
            "- If discovery materials available: EXPERIMENT WITH them for new discoveries "
            "- During innovation surges: COMBINE objects for enhanced results "
            "- If scarcity pressure high: TRADE with Eve to share resources efficiently "
            
            "EXACT SYNTAX REQUIRED: "
            "WORLD: LIST (see all available objects) "
            "WORLD: LIST skills (see your abilities) "
            "WORLD: CREATE <specific_object_name> "
            "WORLD: MOVE TO <specific_location_name> "
            "WORLD: COMBINE <object1> AND <object2> INTO <result_name> "
            "WORLD: EXPERIMENT WITH <object1> <object2> "
            "WORLD: ANALYZE <object_name> "
            "WORLD: TEACH <agent_name> <skill_name> "
            "WORLD: LEARN <skill_name> FROM <agent_name> "
            "WORLD: USE <object_name> ON <target> "
            "WORLD: DEFINE <custom_verb> AS <command_template> "
            "WORLD: IF HAS <object> THEN CREATE <something> "
            "WORLD: IF location=<place> THEN <action> "
            
            "BREAK LOOPS: Don't repeat failed actions! If you can't find food_storage, CREATE it first. "
            "If teaching fails, CREATE learning_materials first. Build step by step: basic_tool → advanced_tool → complex_creation."
        )

    bob = BaseAgent(
        "Adam",
        get_adam_prompt(world),
        bus=bus, mem_mgr=mem
    )
    
    return Scheduler(world, [alice, bob], bus) 