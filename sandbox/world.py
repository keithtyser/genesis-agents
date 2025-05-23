from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List
import json, os, tempfile, random
from uuid import uuid4
from datetime import datetime


@dataclass
class WorldState:
    tick: int = 0
    objects: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    agents: Dict[str, Dict[str, Any]]  = field(default_factory=dict)
    verbs: Dict[str, str] = field(default_factory=dict)
    
    # NEW: Environmental dynamics and loop detection
    environment: Dict[str, Any] = field(default_factory=lambda: {
        "weather": "clear",
        "season": "spring", 
        "resources": {"wood": 100, "stone": 80, "water": 100, "food": 60},
        "active_events": [],
        "event_history": [],
        "innovation_rewards": [],
        "discovery_materials": [],
        "scarcity_pressure": 0
    })
    agent_action_history: Dict[str, List[str]] = field(default_factory=dict)
    current_focus: str = "exploration"  # rotation: exploration, survival, innovation, cooperation
    focus_change_tick: int = 0

    # -------------------------------------------------------------- #
    def add_object(self, kind: str, props: Dict[str, Any] | None = None) -> str:
        """
        Add an object of given kind; return its 8-char uuid.
        """
        oid = uuid4().hex[:8]
        self.objects[oid] = {"kind": kind, **(props or {})}
        return oid

    # -------------------------------------------------------------- #
    def trigger_environmental_event(self) -> str | None:
        """
        Randomly trigger environmental events to create pressure and variety.
        """
        if random.random() < 0.15:  # 15% chance per tick
            events = [
                {"type": "storm", "description": "A fierce storm damages exposed objects", "duration": 3},
                {"type": "abundance", "description": "Rich resources discovered nearby", "duration": 5},
                {"type": "scarcity", "description": "Resources become harder to find", "duration": 4},
                {"type": "inspiration", "description": "Sudden creative insights emerge", "duration": 2},
                {"type": "tool_wear", "description": "Tools show signs of wear and need maintenance", "duration": 1},
                {"type": "discovery", "description": "Strange materials found in the area", "duration": 3},
                {"type": "innovation_surge", "description": "Creative energy fills the air, combinations yield surprising results", "duration": 4},
                {"type": "material_shortage", "description": "Basic materials become scarce, cooperation is essential", "duration": 6},
                {"type": "discovery_cache", "description": "Ancient cache of mysterious objects discovered", "duration": 2}
            ]
            
            event = random.choice(events)
            event["start_tick"] = self.tick
            event["end_tick"] = self.tick + event["duration"]
            
            self.environment["active_events"].append(event)
            self.environment["event_history"].append(event.copy())
            
            # Apply immediate effects
            if event["type"] == "storm":
                # Damage some exposed objects
                for oid, obj in self.objects.items():
                    if random.random() < 0.3 and "shelter" not in obj.get("kind", ""):
                        obj["damaged"] = True
            elif event["type"] == "abundance":
                for resource in self.environment["resources"]:
                    self.environment["resources"][resource] += 20
            elif event["type"] == "scarcity":
                for resource in self.environment["resources"]:
                    self.environment["resources"][resource] = max(10, self.environment["resources"][resource] - 15)
            elif event["type"] == "discovery":
                # Add special materials
                self.environment["resources"]["rare_minerals"] = self.environment["resources"].get("rare_minerals", 0) + 10
            elif event["type"] == "innovation_surge":
                # Boost combination success and add special materials as actual objects
                special_materials = ["crystal_shard", "ancient_gear", "energy_core"]
                for material in special_materials:
                    props = {
                        "description": f"A mysterious {material.replace('_', ' ')} pulsing with energy",
                        "location": "energy_nexus",
                        "creator": "cosmic",
                        "discoverable": True,
                        "rarity": "legendary",
                        "energy_level": "high"
                    }
                    oid = self.add_object(material, props)
                    self.environment["discovery_materials"].append(material)
            elif event["type"] == "material_shortage":
                # Reduce basic resources to encourage cooperation
                for resource in ["wood", "stone"]:
                    self.environment["resources"][resource] = max(5, self.environment["resources"][resource] - 30)
                self.environment["scarcity_pressure"] += 3
            elif event["type"] == "discovery_cache":
                # Add rare discovery materials as actual findable objects
                cache_items = ["mysterious_blueprint", "strange_alloy", "forgotten_tool"]
                for item in cache_items:
                    # Create actual objects that can be found and analyzed
                    props = {
                        "description": f"A rare {item.replace('_', ' ')} with unknown properties",
                        "location": "hidden_cave",
                        "creator": "ancient",
                        "discoverable": True,
                        "rarity": "rare"
                    }
                    oid = self.add_object(item, props)
                    # Also add to discovery_materials list for context
                    self.environment["discovery_materials"].append(item)
                
            return f"🌍 ENVIRONMENTAL EVENT: {event['description']} (lasts {event['duration']} ticks)"
        return None

    # -------------------------------------------------------------- #
    def update_environment(self) -> List[str]:
        """
        Update environmental state, expire events, manage resources.
        """
        messages = []
        
        # Remove expired events
        active_events = []
        for event in self.environment["active_events"]:
            if self.tick < event["end_tick"]:
                active_events.append(event)
            else:
                messages.append(f"🌍 Event '{event['type']}' has ended")
        self.environment["active_events"] = active_events
        
        # Natural resource regeneration
        if self.tick % 5 == 0:  # Every 5 ticks
            for resource in ["wood", "stone", "water", "food"]:
                current = self.environment["resources"][resource]
                if current < 100:
                    self.environment["resources"][resource] = min(100, current + 5)
        
        # Decay scarcity pressure over time
        if self.environment["scarcity_pressure"] > 0:
            self.environment["scarcity_pressure"] = max(0, self.environment["scarcity_pressure"] - 0.5)
        
        # Season progression (every 25 ticks, but only check once per season)
        season_length = 25
        current_season_index = self.tick // season_length
        seasons = ["spring", "summer", "autumn", "winter"]
        expected_season = seasons[current_season_index % 4]
        
        if self.environment["season"] != expected_season:
            self.environment["season"] = expected_season
            messages.append(f"🌍 Season changed to {expected_season} (tick {self.tick})")
        
        # Weather changes
        if random.random() < 0.1:  # 10% chance
            weathers = ["clear", "cloudy", "rainy", "windy"]
            new_weather = random.choice(weathers)
            if new_weather != self.environment["weather"]:
                self.environment["weather"] = new_weather
                messages.append(f"🌍 Weather changed to {new_weather}")
        
        return messages

    # -------------------------------------------------------------- #
    def rotate_focus_if_needed(self) -> str | None:
        """
        Rotate world focus to prevent agents from getting stuck in loops.
        """
        if self.tick - self.focus_change_tick >= 15:  # Change focus every 15 ticks
            focuses = ["exploration", "survival", "innovation", "cooperation"]
            current_idx = focuses.index(self.current_focus)
            self.current_focus = focuses[(current_idx + 1) % len(focuses)]
            self.focus_change_tick = self.tick
            return f"🎯 World focus shifted to: {self.current_focus.upper()}"
        return None

    # -------------------------------------------------------------- #
    def detect_agent_loops(self, agent_name: str, action: str) -> bool:
        """
        Detect if an agent is stuck in repetitive unsuccessful actions.
        """
        if agent_name not in self.agent_action_history:
            self.agent_action_history[agent_name] = []
        
        history = self.agent_action_history[agent_name]
        history.append(action)
        
        # Keep only last 12 actions (increased from 10)
        if len(history) > 12:
            history.pop(0)
        
        # Be less aggressive with informational commands
        if any(cmd in action for cmd in ["LIST", "has no skills", "sees available", "sees agents"]):
            # For informational commands, require more repetitions and longer history
            if len(history) >= 10:
                recent_actions = history[-10:]
                unique_actions = set(recent_actions)
                # Only trigger if literally the same command 8+ times in a row
                if len(unique_actions) <= 1 and len([a for a in recent_actions if "LIST" in a or "has no" in a]) >= 8:
                    return True
            return False
        
        # For other commands, use standard detection but be less aggressive
        if len(history) >= 10:  # Increased from 8
            recent_actions = history[-8:]
            unique_actions = set(recent_actions)
            # Only trigger if truly stuck (same action 6+ times)
            if len(unique_actions) <= 1 and len(recent_actions) >= 6:
                return True
        return False

    # -------------------------------------------------------------- #
    def get_environmental_context(self) -> str:
        """
        Get current environmental context for agents.
        """
        context = []
        
        # Current conditions
        context.append(f"🌍 Environment: {self.environment['weather']} weather, {self.environment['season']} season")
        
        # Resource status
        resources = self.environment["resources"]
        low_resources = [r for r, v in resources.items() if v < 30]
        if low_resources:
            context.append(f"⚠️ Resources running low: {', '.join(low_resources)}")
        
        # Active events
        if self.environment["active_events"]:
            event_descriptions = [e["description"] for e in self.environment["active_events"]]
            context.append(f"🌟 Active events: {'; '.join(event_descriptions)}")
        
        # Current focus
        context.append(f"🎯 Current world focus: {self.current_focus.upper()}")
        
        return " | ".join(context)

    # -------------------------------------------------------------- #
    def reward_innovation(self, agent_name: str, innovation_type: str, details: str) -> str:
        """
        Track and reward innovative behaviors to encourage more complex actions.
        """
        reward = {
            "agent": agent_name,
            "type": innovation_type,
            "details": details,
            "tick": self.tick,
            "reward_value": 0
        }
        
        # Calculate reward value based on innovation type
        if innovation_type == "COMBINE":
            reward["reward_value"] = 3
            # Add discovery materials as reward
            if "crystal_shard" not in self.environment["discovery_materials"]:
                self.environment["discovery_materials"].append("crystal_shard")
        elif innovation_type == "EXPERIMENT":
            reward["reward_value"] = 5
            # Add rare materials
            self.environment["discovery_materials"].extend(["experiment_residue", "new_compound"])
        elif innovation_type == "DEFINE":
            reward["reward_value"] = 4
            # Increase innovation surge chance
            if len(self.environment["active_events"]) < 2:
                innovation_event = {
                    "type": "innovation_surge",
                    "description": "Your innovation inspires creative energy throughout the world",
                    "duration": 3,
                    "start_tick": self.tick,
                    "end_tick": self.tick + 3
                }
                self.environment["active_events"].append(innovation_event)
        elif innovation_type == "TRADE":
            reward["reward_value"] = 2
            # Reduce scarcity pressure
            self.environment["scarcity_pressure"] = max(0, self.environment["scarcity_pressure"] - 1)
        
        self.environment["innovation_rewards"].append(reward)
        return f"🎉 INNOVATION REWARD: {agent_name} gained {reward['reward_value']} innovation points for {innovation_type}!"

    # -------------------------------------------------------------- #
    def get_innovation_context(self) -> str:
        """
        Get context about available discovery materials and innovation opportunities.
        """
        context_parts = []
        
        # Available discovery materials
        if self.environment["discovery_materials"]:
            materials = list(set(self.environment["discovery_materials"]))[:3]  # Show up to 3 unique
            context_parts.append(f"🔬 Available discovery materials: {', '.join(materials)}")
        
        # Scarcity pressure
        if self.environment["scarcity_pressure"] > 2:
            context_parts.append(f"⚠️ HIGH SCARCITY PRESSURE: Cooperation and resource sharing needed!")
        elif self.environment["scarcity_pressure"] > 0:
            context_parts.append(f"⚠️ Resource pressure: Consider trading and efficient use")
        
        # Innovation opportunities
        innovation_surge_active = any(e["type"] == "innovation_surge" for e in self.environment["active_events"])
        if innovation_surge_active:
            context_parts.append("🚀 INNOVATION SURGE: Perfect time for COMBINE and EXPERIMENT actions!")
        
        return " | ".join(context_parts) if context_parts else ""

    # -------------------------------------------------------------- #
    def save(self, path: str = "world.json") -> None:
        """
        Atomically write JSON to disk (temp file + replace).
        Converts datetime objects to ISO-8601 strings automatically.
        Optionally saves snapshots to snapshots/ directory every SNAP_EVERY ticks.
        """
        def _dt_handler(o):
            if isinstance(o, datetime):
                return o.isoformat()
            raise TypeError

        data = asdict(self)
        json_str = json.dumps(data, indent=2, default=_dt_handler)

        # Save the main world state file
        dir_ = os.path.dirname(path) or "."
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False, dir=dir_
        ) as tmp:
            tmp.write(json_str)
            tmp_path = tmp.name
        os.replace(tmp_path, path)

        # Check for snapshot rotation based on environment variable
        snap_every = int(os.environ.get('SNAP_EVERY', 500))
        if snap_every > 0 and self.tick > 0 and self.tick % snap_every == 0:
            snapshot_dir = 'snapshots'
            if not os.path.exists(snapshot_dir):
                os.makedirs(snapshot_dir)
            snapshot_path = os.path.join(snapshot_dir, f'world_{self.tick}.json')
            with open(snapshot_path, 'w', encoding='utf-8') as f:
                f.write(json_str)

    # -------------------------------------------------------------- #
    @classmethod
    def load(cls, path: str = "world.json") -> "WorldState":
        """
        Load file if it exists; otherwise return a fresh WorldState().
        """
        if not os.path.exists(path):
            return cls()
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        instance = cls(
            tick=data.get("tick", 0),
            objects=data.get("objects", {}),
            agents=data.get("agents", {}),
            verbs=data.get("verbs", {}),
        )
        
        # Load environment data if it exists
        if "environment" in data:
            instance.environment.update(data["environment"])
        if "agent_action_history" in data:
            instance.agent_action_history = data["agent_action_history"]
        if "current_focus" in data:
            instance.current_focus = data["current_focus"]
        if "focus_change_tick" in data:
            instance.focus_change_tick = data["focus_change_tick"]
            
        return instance 