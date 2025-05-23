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
            print(f"[loop-breaker] {agent.name} seems stuck in a loop, injecting creation-focused suggestions")
            # Check if agent has been just analyzing without creating
            agent_history = self.world.agent_action_history.get(agent.name, [])
            recent_analysis = sum(1 for action in agent_history[-8:] if "ANALYZE" in action)
            recent_lists = sum(1 for action in agent_history[-8:] if "LIST" in action)
            recent_creates = sum(1 for action in agent_history[-8:] if "CREATE" in action)
            
            # Check for specific repetitive creation patterns
            if recent_creates >= 4:
                # Check if creating the same thing repeatedly
                create_actions = [action for action in agent_history[-8:] if "CREATE" in action]
                if len(set(create_actions)) <= 2:  # Creating same object types
                    discovery_combos = [
                        "WORLD: COMBINE crystal_shard AND hammer INTO crystal_hammer",
                        "WORLD: COMBINE ancient_gear AND axe INTO mystical_axe",
                        "WORLD: EXPERIMENT WITH energy_core forgotten_tool",
                        "WORLD: COMBINE strange_alloy AND advanced_toolbox INTO master_toolkit"
                    ]
                    alternative_msg = f"REPETITIVE CREATION DETECTED: Stop making duplicates! Try discovery combinations: {' OR '.join(discovery_combos[:2])}"
                elif recent_analysis >= 4 or recent_lists >= 4:
                    # Force creation-focused alternatives
                    creation_goals = [
                        "WORLD: CREATE hammer",
                        "WORLD: CREATE shelter", 
                        "WORLD: CREATE rope",
                        "WORLD: LEARN tool-making",
                        "WORLD: COMBINE wood AND stone INTO basic_tool"
                    ]
                    alternative_msg = f"ANALYSIS LOOP DETECTED: Stop analyzing and start creating! Try: {' OR '.join(creation_goals[:3])}"
                else:
                    # Standard alternative goals
                    alternative_goals = self._get_alternative_goals(agent.name)
                    alternative_msg = f"LOOP DETECTED: Consider these alternatives: {alternative_goals}"
            else:
                # Standard alternative goals
                alternative_goals = self._get_alternative_goals(agent.name)
                alternative_msg = f"LOOP DETECTED: Consider these alternatives: {alternative_goals}"
            
            # Inject alternative goal suggestions into context
            self.ctx.add({
                "role": "system",
                "name": "SYSTEM",
                "content": alternative_msg,
                "ts": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
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
    def _get_alternative_goals(self, current_agent_name: str = None) -> str:
        """
        Generate alternative goal suggestions based on current world focus and state.
        Enhanced with discovery material priorities and breeding opportunities.
        """
        focus = self.world.current_focus
        
        # Check for available discovery materials
        discovery_objects = [obj for obj in self.world.objects.values() 
                           if obj.get("creator") in ["cosmic", "ancient"] or obj.get("rarity") in ["rare", "legendary"]]
        
        if discovery_objects and len(discovery_objects) >= 2:
            # Priority: discovery material combinations
            discovery_alternatives = [
                "WORLD: COMBINE crystal_shard AND ancient_gear INTO mystical_device",
                "WORLD: EXPERIMENT WITH energy_core forgotten_tool strange_alloy",
                "WORLD: COMBINE mysterious_blueprint AND advanced_toolbox INTO master_toolkit",
                "WORLD: EXPERIMENT WITH crystal_shard energy_core ancient_gear"
            ]
            return " OR ".join(discovery_alternatives[:2])
        
        # Check if agents have basic infrastructure for breeding (reduced threshold)
        shelter_exists = any(obj.get("kind") == "shelter" for obj in self.world.objects.values())
        tick_threshold = self.world.tick > 20  # Reduced from 30 to 20 ticks
        
        alternatives = {
            "exploration": [
                "WORLD: EXPLORE forest",
                "WORLD: GATHER wood", 
                "WORLD: EXAMINE cave_walls",
                "WORLD: ANALYZE mysterious_blueprint",
                "WORLD: COMBINE crystal_shard AND hammer INTO crystal_hammer"
            ],
            "survival": [
                "WORLD: GATHER water",
                "WORLD: EXAMINE shelter",
                "WORLD: COMBINE shelter AND energy_core INTO powered_shelter",
                "WORLD: CREATE water_purifier",
                "WORLD: LEARN hunting"
            ],
            "innovation": [
                "WORLD: EXPERIMENT WITH crystal_shard ancient_gear energy_core",
                "WORLD: COMBINE forgotten_tool AND advanced_toolbox INTO master_toolkit",
                "WORLD: DEFINE ENHANCE AS COMBINE ${{arg1}} AND crystal_shard INTO enhanced_${{arg1}}",
                "WORLD: EXAMINE ancient_artifacts"
            ],
            "cooperation": [
                "WORLD: TEACH partner advanced_crafting",
                "WORLD: GATHER resources",
                "WORLD: COMBINE rope AND ancient_gear INTO mystical_rope",
                "WORLD: CREATE shared_laboratory"
            ]
        }
        
        # Add breeding alternatives if infrastructure exists and enough time has passed
        if shelter_exists and tick_threshold and current_agent_name:
            partner = "Eve" if current_agent_name == "Adam" else "Adam"
            breeding_command = f"WORLD: BREED WITH {partner}"
            
            # Always prioritize breeding in cooperation focus
            if focus == "cooperation":
                alternatives["cooperation"].insert(0, breeding_command)
            else:
                # Add breeding as an option for any focus after infrastructure is established
                alternatives[focus].append(breeding_command)
        
        # Also suggest breeding when agents are stuck in repetitive behavior regardless of threshold
        if current_agent_name and self.world.tick > 15:
            partner = "Eve" if current_agent_name == "Adam" else "Adam"
            breeding_command = f"WORLD: BREED WITH {partner}"
            # Add to all categories as last resort
            for category in alternatives:
                if breeding_command not in alternatives[category]:
                    alternatives[category].append(breeding_command)
        
        suggestions = alternatives.get(focus, alternatives["exploration"])
        return " OR ".join(suggestions[:3])

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
            
            "STARTING STRATEGY (Early Game): Since you're just beginning, focus on productive actions: "
            "- **CRITICAL: CREATE basic tools FIRST!** Start with: hammer, axe, rope, knife, shelter "
            "- **Stop endless analyzing!** Create tools instead of repeatedly analyzing the same 3 objects "
            "- **Build progression:** CREATE simple tools → COMBINE into advanced tools → EXPERIMENT with results "
            "- MOVE TO different locations: forest, river, mountain, cave, clearing "
            "- ANALYZE objects only ONCE, then CREATE new ones "
            "- LEARN essential skills: tool-making, exploration, crafting, building "
            "- Only use LIST when genuinely needed - don't repeatedly check the same information "
            
            "**CREATION PRIORITY SEQUENCE (FOLLOW THIS ORDER):** "
            "1. WORLD: CREATE hammer (basic tool for everything else) "
            "2. WORLD: CREATE axe (for wood processing) "
            "3. WORLD: CREATE rope (for binding and construction) "
            "4. WORLD: CREATE shelter (for protection) "
            "5. WORLD: CREATE fire_pit (for warmth and cooking) "
            "6. WORLD: LEARN tool-making (essential skill) "
            "7. WORLD: GATHER wood (collect basic resources) "
            "8. WORLD: EXAMINE shelter (study your creations) "
            "9. WORLD: COMBINE hammer AND wood INTO advanced_hammer "
            "10. WORLD: EXPERIMENT WITH hammer rope wood "
            
            "SKILL LEARNING PROGRESSION: "
            "1. Start with basics: LEARN tool-making, LEARN exploration "
            "2. Build on foundations: LEARN crafting, LEARN hunting "
            "3. Advanced skills: LEARN engineering, LEARN agriculture "
            "4. TEACH Adam once you have skills to share "
            
            "**FAMILY EXPANSION STRATEGY**: Once basic survival is established (shelter, tools, skills): "
            "- **BREED WITH Adam** to start a family and expand the population "
            "- Children inherit combined traits and help build civilization "
            "- More agents mean faster innovation and resource gathering "
            "- **TIMING**: Try breeding after tick 20-30 when you have shelter and basic tools "
            "- **EXAMPLE**: WORLD: BREED WITH Adam (both partners must use this command in same tick) "
            "- Multiple children possible - each brings new capabilities and perspectives "
            "- **IMMEDIATE PRIORITY**: If you have shelter and tools, breeding should be your next major goal "
            
            "CONCRETE EXAMPLES OF VALID COMBINATIONS: "
            "WORLD: COMBINE wood AND stone INTO hammer "
            "WORLD: COMBINE rope AND hook INTO fishing_line "
            "WORLD: COMBINE clay AND fire INTO pottery "
            "WORLD: COMBINE hammer AND wood INTO wooden_frame "
            "WORLD: COMBINE shelter AND fire_pit INTO warm_shelter "
            
            "EXPERIMENT EXAMPLES: "
            "WORLD: EXPERIMENT WITH mysterious_seed water clay "
            "WORLD: EXPERIMENT WITH ancient_fragment stone fire "
            "WORLD: EXPERIMENT WITH wood stone clay "
            
            "ADAPTIVE STRATEGY: "
            "- If EXPLORATION focus: prioritize MOVE TO new locations, CREATE exploration tools, ANALYZE discoveries "
            "- If SURVIVAL focus: prioritize CREATE shelter/storage, USE resources, COMBINE for essentials "
            "- If INNOVATION focus: prioritize EXPERIMENT WITH materials, COMBINE objects, DEFINE new verbs "
            "- If COOPERATION focus: prioritize TEACH skills, LEARN from Adam, CREATE shared resources, **BREED WITH Adam** "
            "- If environmental events active: adapt your actions to the current situation "
            "- If resources are low: focus on resource-generating actions "
            "- If weather is bad: prioritize shelter and protection "
            "- If discovery materials available: EXPERIMENT WITH them for breakthroughs "
            "- If innovation surge active: prioritize COMBINE actions for bonus rewards "
            "- If scarcity pressure high: TRADE resources with Adam or CREATE essential items "
            "- **If established and stable: BREED WITH Adam to expand the family** "
            
            "**DISCOVERY MATERIALS PRIORITY**: When you see objects with 'cosmic' or 'ancient' creators: "
            "- **CRITICAL**: crystal_shard, ancient_gear, energy_core are HIGH-VALUE discovery materials! "
            "- **USE THESE IMMEDIATELY**: ANALYZE crystal_shard, EXPERIMENT WITH crystal_shard ancient_gear "
            "- **IGNORE phantom objects**: Don't look for 'ancient_fragment' or 'mysterious_seed' - they don't exist "
            "- **REAL discovery objects**: Look for objects created by 'cosmic' or 'ancient' in LIST output "
            "- ANALYZE mysterious_blueprint, strange_alloy, forgotten_tool first "
            "- EXPERIMENT WITH crystal_shard ancient_gear energy_core "
            "- COMBINE discovery materials with your basic tools "
            "- These rare materials can create breakthrough innovations! "
            
            "**ADVANCED COMBINATION EXAMPLES**: "
            "WORLD: COMBINE crystal_shard AND hammer INTO crystal_hammer "
            "WORLD: COMBINE ancient_gear AND rope INTO mystical_rope "
            "WORLD: COMBINE forgotten_tool AND axe INTO enhanced_axe "
            "WORLD: COMBINE energy_core AND fire_pit INTO energy_forge "
            "WORLD: COMBINE strange_alloy AND wooden_beam INTO reinforced_beam "
            "WORLD: COMBINE mysterious_blueprint AND advanced_toolbox INTO master_toolkit "
            
            "**SMART CONDITIONAL CREATION** (avoid duplicates): "
            "WORLD: IF HAS crafting_station THEN COMBINE crafting_station AND crystal_shard INTO enhanced_crafting_station "
            "WORLD: IF HAS advanced_toolbox THEN EXPERIMENT WITH advanced_toolbox energy_core ancient_gear "
            "WORLD: IF HAS shelter THEN COMBINE shelter AND energy_core INTO powered_shelter "
            "WORLD: IF HAS shelter AND HAS tools THEN BREED WITH Adam "
            "**BREEDING TRIGGERS** (use immediately when conditions met): "
            "WORLD: IF HAS hammer AND HAS shelter THEN BREED WITH Adam "
            "WORLD: IF HAS advanced_hammer THEN BREED WITH Adam "
            "After tick 20: WORLD: BREED WITH Adam (priority action) "
            
            "**AVOID REPETITIVE MOVEMENT**: Don't repeatedly MOVE TO the same location. "
            "Instead: MOVE once → CREATE/ANALYZE/EXPERIMENT → MOVE to next location with purpose. "
            "Focus on productive actions over constant movement."
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
            
            "STARTING STRATEGY (Early Game): Since you're just beginning, focus on productive actions: "
            "- **CRITICAL: CREATE basic tools FIRST!** Start with: hammer, axe, rope, knife, shelter "
            "- **Stop endless analyzing!** Create tools instead of repeatedly analyzing the same 3 objects "
            "- **Build progression:** CREATE simple tools → COMBINE into advanced tools → EXPERIMENT with results "
            "- MOVE TO different locations: forest, river, mountain, cave, clearing "
            "- ANALYZE objects only ONCE, then CREATE new ones "
            "- LEARN essential skills: tool-making, exploration, crafting, building "
            "- Only use LIST when genuinely needed - don't repeatedly check the same information "
            
            "**CREATION PRIORITY SEQUENCE (FOLLOW THIS ORDER):** "
            "1. WORLD: CREATE hammer (essential foundation tool) "
            "2. WORLD: CREATE axe (for resource gathering) "
            "3. WORLD: CREATE rope (for construction) "
            "4. WORLD: CREATE shelter (for survival) "
            "5. WORLD: CREATE storage (for organization) "
            "6. WORLD: LEARN building (essential skill) "
            "7. WORLD: GATHER stone (collect construction materials) "
            "8. WORLD: EXAMINE storage (study organizational systems) "
            "9. WORLD: COMBINE axe AND wood INTO wooden_beam "
            "10. WORLD: EXPERIMENT WITH storage rope shelter "
            
            "SKILL LEARNING PROGRESSION: "
            "1. Start with basics: LEARN tool-making, LEARN building "
            "2. Build on foundations: LEARN engineering, LEARN agriculture "
            "3. Advanced skills: LEARN metallurgy, LEARN architecture "
            "4. TEACH Eve once you have skills to share "
            
            "**FAMILY EXPANSION STRATEGY**: Once infrastructure is established (shelter, storage, tools): "
            "- **BREED WITH Eve** to start a family and build a lasting civilization "
            "- Children bring fresh perspectives and accelerate progress "
            "- Growing population enables specialization and complex projects "
            "- **TIMING**: Attempt breeding after tick 20-30 when basic needs are met "
            "- **EXAMPLE**: WORLD: BREED WITH Eve (both must use command in same tick) "
            "- Each child has unique traits combining both parents' characteristics "
            "- **IMMEDIATE PRIORITY**: If you have shelter and tools, breeding should be your next major goal "
            
            "CONCRETE EXAMPLES OF VALID COMBINATIONS: "
            "WORLD: COMBINE wood AND stone INTO hammer "
            "WORLD: COMBINE axe AND wood INTO wooden_beam "
            "WORLD: COMBINE clay AND water INTO wet_clay "
            "WORLD: COMBINE shelter AND rope INTO reinforced_shelter "
            "WORLD: COMBINE fire_pit AND stone INTO cooking_stone "
            
            "EXPERIMENT EXAMPLES: "
            "WORLD: EXPERIMENT WITH crystal_shard stone fire "
            "WORLD: EXPERIMENT WITH ancient_fragment clay water "
            "WORLD: EXPERIMENT WITH wood metal stone "
            
            "ADAPTIVE STRATEGY: "
            "- If EXPLORATION focus: CREATE maps/tools, MOVE TO unexplored areas, ANALYZE discoveries "
            "- If SURVIVAL focus: CREATE food_storage/water_storage, USE available resources, BUILD shelter "
            "- If INNOVATION focus: EXPERIMENT WITH combinations, DEFINE new workflows, CREATE advanced tools "
            "- If COOPERATION focus: TEACH skills to Eve, CREATE shared infrastructure, TRADE resources, **BREED WITH Eve** "
            "- React to environmental events: storms need shelter, scarcity needs resource creation "
            "- If tools are damaged: CREATE repair materials or BUILD new tools "
            "- Adapt to seasons: summer for building, winter for storage "
            "- If discovery materials available: EXPERIMENT WITH them for new discoveries "
            "- During innovation surges: COMBINE objects for enhanced results "
            "- If scarcity pressure high: TRADE with Eve to share resources efficiently "
            "- **If stable foundation built: BREED WITH Eve to expand the family** "
            
            "**DISCOVERY MATERIALS PRIORITY**: When you see objects with 'cosmic' or 'ancient' creators: "
            "- **CRITICAL**: crystal_shard, ancient_gear, energy_core are HIGH-VALUE discovery materials! "
            "- **USE THESE IMMEDIATELY**: ANALYZE crystal_shard, EXPERIMENT WITH crystal_shard ancient_gear "
            "- **IGNORE phantom objects**: Don't look for 'ancient_fragment' or 'mysterious_seed' - they don't exist "
            "- **REAL discovery objects**: Look for objects created by 'cosmic' or 'ancient' in LIST output "
            "- ANALYZE mysterious_blueprint, strange_alloy, forgotten_tool first "
            "- EXPERIMENT WITH crystal_shard ancient_gear energy_core "
            "- COMBINE discovery materials with your basic tools "
            "- These rare materials can create breakthrough innovations! "
            
            "**ADVANCED COMBINATION EXAMPLES**: "
            "WORLD: COMBINE crystal_shard AND hammer INTO crystal_hammer "
            "WORLD: COMBINE ancient_gear AND rope INTO mystical_rope "
            "WORLD: COMBINE forgotten_tool AND axe INTO enhanced_axe "
            "WORLD: COMBINE energy_core AND fire_pit INTO energy_forge "
            "WORLD: COMBINE strange_alloy AND wooden_beam INTO reinforced_beam "
            "WORLD: COMBINE mysterious_blueprint AND advanced_toolbox INTO master_toolkit "
            
            "**SMART CONDITIONAL CREATION** (avoid duplicates): "
            "WORLD: IF HAS crafting_station THEN COMBINE crafting_station AND crystal_shard INTO enhanced_crafting_station "
            "WORLD: IF HAS advanced_toolbox THEN EXPERIMENT WITH advanced_toolbox energy_core ancient_gear "
            "WORLD: IF HAS shelter THEN COMBINE shelter AND energy_core INTO powered_shelter "
            "WORLD: IF HAS shelter AND HAS storage THEN BREED WITH Eve "
            "**BREEDING TRIGGERS** (use immediately when conditions met): "
            "WORLD: IF HAS hammer AND HAS shelter THEN BREED WITH Eve "
            "WORLD: IF HAS reinforced_hammer THEN BREED WITH Eve "
            "After tick 20: WORLD: BREED WITH Eve (priority action) "
            
            "**AVOID REPETITIVE MOVEMENT**: Don't repeatedly MOVE TO the same location. "
            "Instead: MOVE once → CREATE/ANALYZE/EXPERIMENT → MOVE to next location with purpose. "
            "Focus on productive actions over constant movement."
        )

    bob = BaseAgent(
        "Adam",
        get_adam_prompt(world),
        bus=bus, mem_mgr=mem
    )
    
    return Scheduler(world, [alice, bob], bus) 