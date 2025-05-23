"""
sandbox.commands – enhanced WORLD: directive handler with expanded action space.

# Enhanced Verbs & syntax
# -----------------------
# WORLD: CREATE <kind> [key=value ...]
# WORLD: MOVE TO <location>
# WORLD: SET <key>=<value>
# WORLD: BREED WITH <partner>
# WORLD: TEACH <agent> <skill/knowledge>
# WORLD: LEARN <skill> [FROM <agent>]
# WORLD: TRADE <item> FOR <item> WITH <agent>
# WORLD: DESTROY <object_id>
# WORLD: COMBINE <obj1> AND <obj2> [INTO <result>]
# WORLD: ANALYZE <object_id>
# WORLD: EXPERIMENT WITH <items...>
# WORLD: USE <object_id> [ON <target>]
# WORLD: MODIFY <object_id> <property>=<value>
# WORLD: INSPECT <object_id>
# WORLD: IF <condition> THEN <action>
# WORLD: DEFINE <verb> AS <template>

# Function
# --------
#     execute(world, bus, speaker, content) -> list[str]  # events log
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
import re, uuid, random

_PATTERN = re.compile(r"^WORLD:\s*(.+)", re.IGNORECASE)

CORE_VERBS = {
    "CREATE", "MOVE", "SET", "BREED", "DEFINE", "HELP",
    "TEACH", "LEARN", "TRADE", "DESTROY", "COMBINE", 
    "ANALYZE", "EXPERIMENT", "USE", "MODIFY", "INSPECT", "IF"
}


def _kv_pairs(tokens: List[str]) -> Dict[str, str]:
    """Return dict for tokens that look like key=value."""
    kv = {}
    for tok in tokens:
        if "=" in tok:
            k, v = tok.split("=", 1)
            kv[k] = v
    return kv


def _find_object_by_kind(world, kind: str, creator: Optional[str] = None) -> Optional[str]:
    """Find object ID by kind, optionally filtered by creator."""
    for oid, obj in world.objects.items():
        if obj.get("kind", "").lower() == kind.lower():
            if creator is None or obj.get("creator") == creator:
                return oid
    return None


def _find_agent(world, agent_name: str):
    """Find agent data by name."""
    return world.agents.get(agent_name)


def _evaluate_condition(world, speaker: str, condition: str) -> bool:
    """Evaluate simple conditions for IF statements."""
    condition = condition.strip()
    
    # Handle "HAS <object>" conditions
    if condition.upper().startswith("HAS "):
        obj_kind = condition[4:].strip()
        return _find_object_by_kind(world, obj_kind, speaker) is not None
    
    # Handle "location=<value>" conditions
    if "=" in condition:
        key, value = condition.split("=", 1)
        agent_data = world.agents.get(speaker, {})
        return str(agent_data.get(key, "")).lower() == value.lower()
    
    # Handle "EXISTS <object>" conditions
    if condition.upper().startswith("EXISTS "):
        obj_kind = condition[7:].strip()
        return _find_object_by_kind(world, obj_kind) is not None
    
    return False


def _normalize_skill(skill: str) -> str:
    """Normalize skill names for consistent matching."""
    return skill.lower().replace("-", "").replace("_", "").replace(" ", "").strip()


def _get_agent_skills(world, agent: str) -> List[str]:
    """Get list of skills an agent has learned."""
    agent_data = world.agents.get(agent, {})
    return agent_data.get("skills", [])


def _add_agent_skill(world, agent: str, skill: str):
    """Add a skill to an agent's skill list."""
    agent_data = world.agents.setdefault(agent, {})
    skills = agent_data.get("skills", [])
    if skill not in skills:
        skills.append(skill)
        agent_data["skills"] = skills


def _get_agent_knowledge(world, agent: str) -> Dict[str, Any]:
    """Get agent's knowledge base."""
    agent_data = world.agents.get(agent, {})
    return agent_data.get("knowledge", {})


def _add_agent_knowledge(world, agent: str, topic: str, content: str):
    """Add knowledge to an agent's knowledge base."""
    agent_data = world.agents.setdefault(agent, {})
    knowledge = agent_data.get("knowledge", {})
    knowledge[topic] = content
    agent_data["knowledge"] = knowledge


# ------------------------------------------------------------------ #
def execute(world, bus, speaker: str, content: str) -> List[str]:
    """
    Parse *content* line-by-line, mutate `world`, publish on `bus`,
    and return a list of human-readable event strings.
    """
    events: List[str] = []

    for line in content.splitlines():
        m = _PATTERN.match(line.strip())
        if not m:
            continue

        command = m.group(1)
        parts = command.split()
        verb = parts[0].upper()
        remainder = parts[1:]

        # Handle conditional statements first
        if verb == "IF" and "THEN" in [p.upper() for p in parts]:
            try:
                then_idx = next(i for i, p in enumerate(parts) if p.upper() == "THEN")
                condition_parts = parts[1:then_idx]
                action_parts = parts[then_idx + 1:]
                
                condition = " ".join(condition_parts)
                action = " ".join(action_parts)
                
                if _evaluate_condition(world, speaker, condition):
                    # Execute the action part recursively
                    sub_events = execute(world, bus, speaker, f"WORLD: {action}")
                    events.extend(sub_events)
                    events.append(f"{speaker} executed conditional: IF {condition} THEN {action}")
                else:
                    events.append(f"{speaker} condition not met: {condition}")
            except (StopIteration, IndexError):
                events.append(f"{speaker} malformed IF statement")
            continue

        # Handle DEFINE verb
        if verb == "DEFINE" and remainder and "AS" in remainder:
            try:
                idx = remainder.index("AS")
                new_verb = remainder[0].upper()
                template = " ".join(remainder[idx+1:])
                if new_verb in CORE_VERBS or new_verb in world.verbs:
                    events.append(f"{speaker} failed to redefine reserved verb {new_verb}")
                else:
                    # Allow templates to reference any core verb or contain complex logic
                    world.verbs[new_verb] = template
                    events.append(f"{speaker} defined new verb {new_verb}")
                    
                    # Innovation reward for defining new verbs
                    if hasattr(world, 'reward_innovation'):
                        reward_msg = world.reward_innovation(speaker, "DEFINE", f"Defined new verb {new_verb}: {template}")
                        events.append(reward_msg)
            except ValueError:
                events.append(f"{speaker} malformed DEFINE syntax")
            continue

        # Handle custom verbs
        elif verb in world.verbs:
            mapping = world.verbs[verb]
            for i, tok in enumerate(remainder, 1):
                mapping = mapping.replace(f"${{arg{i}}}", tok)
            sub_events = execute(world, bus, speaker, f"WORLD: {mapping}")
            events.extend(sub_events)
            continue

        # Core verb implementations
        elif verb == "CREATE" and remainder:
            kind = None
            rest = []
            for token in remainder:
                if kind is None and token.lower() not in ["a", "an", "the"]:
                    kind = token
                else:
                    rest.append(token)
            if kind is None:
                kind = remainder[0]
            
            # Check for duplicate objects by same creator
            existing_count = sum(1 for obj in world.objects.values() 
                               if obj.get("kind") == kind and obj.get("creator") == speaker)
            
            if existing_count >= 3:
                events.append(f"{speaker} already has {existing_count} {kind}s. Consider creating something different or upgrading existing ones.")
                return events
            elif existing_count >= 2:
                events.append(f"{speaker} already has {existing_count} {kind}s. Consider IF statements to avoid duplicates.")
            
            props = _kv_pairs(rest) | {"creator": speaker, "turn": world.tick}
            oid = world.add_object(kind, props)
            events.append(f"{speaker} created {kind} (id={oid})")

        elif verb == "MOVE" and len(remainder) >= 2 and remainder[0].upper() == "TO":
            loc = remainder[1]
            agent_rec = world.agents.setdefault(speaker, {})
            agent_rec["location"] = loc
            events.append(f"{speaker} moved to {loc}")

        elif verb == "SET" and remainder and "=" in remainder[0]:
            key, value = remainder[0].split("=", 1)
            agent_rec = world.agents.setdefault(speaker, {})
            agent_rec[key] = value
            events.append(f"{speaker} set {key}={value}")

        elif verb == "TEACH" and len(remainder) >= 2:
            student = remainder[0]
            skill_or_knowledge = " ".join(remainder[1:])
            
            # Check if teacher has the skill/knowledge with normalization
            teacher_skills = _get_agent_skills(world, speaker)
            teacher_knowledge = _get_agent_knowledge(world, speaker)
            
            # Normalize skill for matching
            normalized_skill = _normalize_skill(skill_or_knowledge)
            teacher_has_skill = any(_normalize_skill(s) == normalized_skill for s in teacher_skills)
            teacher_has_knowledge = skill_or_knowledge in teacher_knowledge
            
            if teacher_has_skill or teacher_has_knowledge:
                if teacher_has_skill:
                    _add_agent_skill(world, student, skill_or_knowledge)
                else:
                    _add_agent_knowledge(world, student, skill_or_knowledge, teacher_knowledge[skill_or_knowledge])
                events.append(f"{speaker} taught {skill_or_knowledge} to {student}")
            else:
                events.append(f"{speaker} cannot teach {skill_or_knowledge} (not possessed)")

        elif verb == "LEARN" and remainder:
            if "FROM" in [r.upper() for r in remainder]:
                from_idx = next(i for i, r in enumerate(remainder) if r.upper() == "FROM")
                skill = " ".join(remainder[:from_idx])
                teacher = remainder[from_idx + 1] if from_idx + 1 < len(remainder) else None
                
                if teacher:
                    teacher_skills = _get_agent_skills(world, teacher)
                    normalized_skill = _normalize_skill(skill)
                    teacher_has_skill = any(_normalize_skill(s) == normalized_skill for s in teacher_skills)
                    
                    if teacher_has_skill:
                        _add_agent_skill(world, speaker, skill)
                        events.append(f"{speaker} learned {skill} from {teacher}")
                    else:
                        events.append(f"{speaker} cannot learn {skill} from {teacher}")
                else:
                    events.append(f"{speaker} cannot learn {skill} from {teacher}")
            else:
                skill = " ".join(remainder)
                _add_agent_skill(world, speaker, skill)
                events.append(f"{speaker} self-learned {skill}")

        elif verb == "TRADE" and "FOR" in remainder and "WITH" in remainder:
            try:
                for_idx = remainder.index("FOR")
                with_idx = remainder.index("WITH")
                offer_item = " ".join(remainder[:for_idx])
                wanted_item = " ".join(remainder[for_idx+1:with_idx])
                partner = remainder[with_idx+1] if with_idx+1 < len(remainder) else None
                
                # Find objects
                offer_obj = _find_object_by_kind(world, offer_item, speaker)
                wanted_obj = _find_object_by_kind(world, wanted_item, partner)
                
                if offer_obj and wanted_obj and partner:
                    # Execute trade
                    world.objects[offer_obj]["creator"] = partner
                    world.objects[wanted_obj]["creator"] = speaker
                    events.append(f"{speaker} traded {offer_item} for {wanted_item} with {partner}")
                    
                    # Innovation reward for trading
                    if hasattr(world, 'reward_innovation'):
                        reward_msg = world.reward_innovation(speaker, "TRADE", f"Traded {offer_item} for {wanted_item} with {partner}")
                        events.append(reward_msg)
                else:
                    events.append(f"{speaker} trade failed: missing items or partner")
            except (ValueError, IndexError):
                events.append(f"{speaker} malformed TRADE syntax")

        elif verb == "DESTROY" and remainder:
            target = remainder[0]
            obj_id = _find_object_by_kind(world, target, speaker)
            if obj_id and obj_id in world.objects:
                destroyed_obj = world.objects.pop(obj_id)
                events.append(f"{speaker} destroyed {destroyed_obj.get('kind', target)} (id={obj_id})")
            else:
                events.append(f"{speaker} cannot destroy {target} (not found or not owned)")

        elif verb == "COMBINE" and "AND" in remainder:
            try:
                and_idx = remainder.index("AND")
                obj1_name = " ".join(remainder[:and_idx])
                
                into_idx = None
                if "INTO" in remainder:
                    into_idx = remainder.index("INTO")
                    obj2_name = " ".join(remainder[and_idx+1:into_idx])
                    result_name = " ".join(remainder[into_idx+1:])
                else:
                    obj2_name = " ".join(remainder[and_idx+1:])
                    result_name = f"combined_{obj1_name}_{obj2_name}"
                
                # Allow using any available objects, not just owned ones
                obj1_id = _find_object_by_kind(world, obj1_name)
                obj2_id = _find_object_by_kind(world, obj2_name)
                
                if obj1_id and obj2_id:
                    # Remove original objects and create combined object
                    obj1 = world.objects.pop(obj1_id)
                    obj2 = world.objects.pop(obj2_id)
                    
                    combined_props = {
                        "creator": speaker,
                        "turn": world.tick,
                        "components": [obj1.get("kind"), obj2.get("kind")],
                        "combined_from": [obj1_id, obj2_id]
                    }
                    
                    new_id = world.add_object(result_name, combined_props)
                    events.append(f"{speaker} combined {obj1_name} and {obj2_name} into {result_name} (id={new_id})")
                    
                    # Innovation reward for combining
                    if hasattr(world, 'reward_innovation'):
                        reward_msg = world.reward_innovation(speaker, "COMBINE", f"{obj1_name} + {obj2_name} = {result_name}")
                        events.append(reward_msg)
                else:
                    # Provide helpful feedback about available objects
                    available_objects = [obj.get('kind') for obj in world.objects.values()]
                    events.append(f"{speaker} cannot combine: {obj1_name} or {obj2_name} not found. Available: {', '.join(set(available_objects))}")
            except ValueError:
                events.append(f"{speaker} malformed COMBINE syntax")

        elif verb == "ANALYZE" and remainder:
            target = remainder[0]
            obj_id = _find_object_by_kind(world, target)
            if obj_id and obj_id in world.objects:
                obj = world.objects[obj_id]
                analysis = f"Object {target}: kind={obj.get('kind')}, creator={obj.get('creator')}, properties={len(obj)}"
                _add_agent_knowledge(world, speaker, f"analysis_of_{target}", analysis)
                events.append(f"{speaker} analyzed {target}: {analysis}")
            else:
                # Object not found - provide helpful suggestions
                available_objects = []
                if world.objects:
                    available_objects = [obj.get('kind') for obj in world.objects.values()]
                
                if available_objects:
                    events.append(f"{speaker} cannot analyze {target} (not found). Available objects: {', '.join(set(available_objects))}. Try 'LIST' to see all objects.")
                else:
                    events.append(f"{speaker} cannot analyze {target} (not found). No objects exist yet. Try 'CREATE' to make something first.")

        elif verb == "EXPERIMENT" and remainder and remainder[0].upper() == "WITH":
            materials = remainder[1:]
            # Check if materials are available (not necessarily owned by speaker)
            available_materials = []
            discovery_materials = []  # Track cosmic/ancient materials
            for material in materials:
                obj_id = _find_object_by_kind(world, material)  # Remove speaker restriction
                if obj_id:
                    available_materials.append(material)
                    # Check if it's a discovery material
                    obj = world.objects[obj_id]
                    if obj.get("creator") in ["cosmic", "ancient"] or obj.get("rarity") in ["rare", "legendary"]:
                        discovery_materials.append(material)
            
            if available_materials:
                # Higher success rate for discovery materials
                base_chance = 0.4  # Base 40% chance
                if discovery_materials:
                    bonus_chance = len(discovery_materials) * 0.2  # +20% per discovery material
                    success_chance = min(0.9, base_chance + bonus_chance)  # Cap at 90%
                else:
                    success_chance = base_chance
                
                if random.random() < success_chance:
                    # Create more interesting results for discovery materials
                    if discovery_materials:
                        result_prefixes = ["mystical", "enhanced", "powered", "crystal", "ancient", "energy"]
                        prefix = random.choice(result_prefixes)
                        discovery = f"{prefix}_{random.randint(1000, 9999)}"
                    else:
                        discovery = f"experimental_{random.randint(1000, 9999)}"
                    
                    discovery_props = {
                        "creator": speaker,
                        "turn": world.tick,
                        "discovered_using": available_materials
                    }
                    
                    # Add special properties for discovery material experiments
                    if discovery_materials:
                        discovery_props["enhanced"] = True
                        discovery_props["discovery_level"] = len(discovery_materials)
                        discovery_props["rarity"] = "enhanced"
                    
                    new_id = world.add_object(discovery, discovery_props)
                    if discovery_materials:
                        events.append(f"{speaker} experimented with {', '.join(available_materials)} and discovered {discovery} (id={new_id}) - Enhanced by discovery materials!")
                    else:
                        events.append(f"{speaker} experimented with {', '.join(available_materials)} and discovered {discovery} (id={new_id})")
                    
                    # Innovation reward for experimenting
                    if hasattr(world, 'reward_innovation'):
                        reward_msg = world.reward_innovation(speaker, "EXPERIMENT", f"Discovered {discovery} using {', '.join(available_materials)}")
                        events.append(reward_msg)
                else:
                    if discovery_materials:
                        events.append(f"{speaker} experimented with {', '.join(available_materials)} but the discovery materials need more time to reveal their secrets")
                    else:
                        events.append(f"{speaker} experimented with {', '.join(available_materials)} but found nothing new")
            else:
                # Provide helpful feedback about available materials
                available_objects = [obj.get('kind') for obj in world.objects.values()]
                events.append(f"{speaker} cannot experiment: materials not available. Try using: {', '.join(set(available_objects))}")

        elif verb == "USE" and remainder:
            tool = remainder[0]
            target = " ".join(remainder[2:]) if len(remainder) > 2 and remainder[1].upper() == "ON" else None
            
            tool_id = _find_object_by_kind(world, tool, speaker)
            if tool_id:
                tool_obj = world.objects[tool_id]
                # Increment usage counter
                tool_obj["uses"] = tool_obj.get("uses", 0) + 1
                
                if target:
                    events.append(f"{speaker} used {tool} on {target}")
                    # Add skill based on tool usage
                    _add_agent_skill(world, speaker, f"using_{tool}")
                else:
                    events.append(f"{speaker} used {tool}")
                    _add_agent_skill(world, speaker, f"using_{tool}")
            else:
                events.append(f"{speaker} cannot use {tool} (not found or not owned)")

        elif verb == "MODIFY" and len(remainder) >= 2:
            target = remainder[0]
            if "=" in remainder[1]:
                key, value = remainder[1].split("=", 1)
                obj_id = _find_object_by_kind(world, target, speaker)
                if obj_id:
                    world.objects[obj_id][key] = value
                    events.append(f"{speaker} modified {target}: set {key}={value}")
                else:
                    events.append(f"{speaker} cannot modify {target} (not found or not owned)")
            else:
                events.append(f"{speaker} malformed MODIFY syntax")

        elif verb == "INSPECT" and remainder:
            target = remainder[0]
            obj_id = _find_object_by_kind(world, target)
            if obj_id and obj_id in world.objects:
                obj = world.objects[obj_id]
                details = ", ".join([f"{k}={v}" for k, v in obj.items()])
                events.append(f"{speaker} inspected {target}: {details}")
                _add_agent_knowledge(world, speaker, f"inspection_of_{target}", details)
            else:
                events.append(f"{speaker} cannot inspect {target} (not found)")

        elif verb == "BREED" and len(remainder) >= 2 and remainder[0].upper() == "WITH":
            partner = remainder[1]
            payload = {
                "type": "breed_request",
                "parent": speaker,
                "partner": partner,
                "tick": world.tick,
            }
            pub = bus.publish("breed_request", payload)
            import asyncio, inspect
            if inspect.isawaitable(pub):
                try:
                    loop = asyncio.get_running_loop()
                    asyncio.create_task(pub)
                except RuntimeError:
                    pass
            events.append(f"{speaker} asked to breed with {partner}")

        elif verb == "LIST":
            if len(remainder) == 0:
                # List all objects
                if world.objects:
                    obj_list = []
                    for obj_id, obj in world.objects.items():
                        obj_list.append(f"{obj.get('kind', 'unknown')} (id={obj_id[:8]}, by {obj.get('creator', 'unknown')})")
                    events.append(f"{speaker} sees available objects: {', '.join(obj_list)}")
                else:
                    events.append(f"{speaker} sees no objects in the world yet")
            else:
                target = remainder[0].lower()
                if target == "skills":
                    agent_data = world.agents.get(speaker, {})
                    skills = agent_data.get('skills', [])
                    if skills:
                        events.append(f"{speaker} knows skills: {', '.join(skills)}")
                    else:
                        events.append(f"{speaker} has no skills yet")
                elif target == "agents":
                    agents = list(world.agents.keys())
                    events.append(f"{speaker} sees agents: {', '.join(agents)}")
                else:
                    events.append(f"{speaker} cannot list '{target}' (try: LIST, LIST skills, LIST agents)")

        else:
            events.append(f"{speaker} issued unknown directive: {verb}")

    return events 