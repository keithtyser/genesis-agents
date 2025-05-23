# Genesis Agents

![python](https://img.shields.io/badge/Python-3.11+-blue)
![license](https://img.shields.io/badge/License-MIT-green)
![agents](https://img.shields.io/badge/Agents-Multi--Generational-purple)
![commands](https://img.shields.io/badge/Commands-15%2B%20Enhanced-orange)

## What's New 🚀

**Genesis Agents** is a revolutionary AI simulation platform where intelligent LLM agents create civilizations from nothing. Starting with Adam & Eve in an empty world, watch families grow and evolve across generations through:

- **👨‍👩‍👧‍👦 Multi-Generational Families**: Breeding system creates children with inherited traits
- **⚡ Enhanced Discovery Materials**: Crystal shards, ancient gears, energy cores creating breakthrough innovations
- **🧪 Advanced Experimentation**: Discovery materials enable enhanced objects with special properties
- **🌍 Environmental Dynamics**: Seasons, weather, discovery caches driving adaptation
- **🔄 Anti-Loop Technology**: Eliminated analysis paralysis - agents now create continuously
- **🏆 Innovation Rewards System**: Rewards for creativity and breakthrough discoveries
- **🧠 Smart Agent Intelligence**: Context-aware behavior, discovery material prioritization

## Why Genesis Agents

Genesis Agents simulates the emergence of civilization itself. AI agents don't just chat—they **build, explore, innovate, breed, and evolve**. From empty earth to thriving multi-generational societies, witness the birth of artificial civilizations with real family dynamics, inheritance, and cultural evolution.

Agents create sophisticated progressions: survival tools → advanced combinations → enhanced discoveries → family expansion → multi-generational knowledge transfer.

## Quick Start

```powershell
git clone https://github.com/yourusername/genesis-agents.git
cd genesis-agents
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:OPENAI_API_KEY="sk-..."  # set your key
python fresh_start.py         # Begin the genesis simulation
```

## Enhanced Command System

Agents have access to **15+ sophisticated commands** with breeding, family dynamics, and multi-generational intelligence:

### Basic Creation & Exploration
- `CREATE <object>` - Build tools, shelter, resources (with duplicate detection)
- `MOVE TO <location>` - Explore different environments
- `EXPLORE <area>` - Discover new resources and locations
- `GATHER <resource>` - Collect materials from the environment
- `EXAMINE <target>` - Study objects and environmental features

### Family & Social Dynamics
- `BREED WITH <partner>` - Create children with inherited traits
- `TEACH <agent> <skill>` - Transfer knowledge across generations
- `LEARN <skill> [FROM <agent>]` - Acquire abilities from family members
- `TRADE <item> FOR <item> WITH <agent>` - Economic cooperation

### Innovation & Discovery
- `COMBINE <obj1> AND <obj2> [INTO <result>]` - Create advanced objects
- `EXPERIMENT WITH <materials...>` - Enhanced with discovery materials
- `ANALYZE <object>` - Gain detailed knowledge
- `USE <object> [ON <target>]` - Apply tools effectively
- `MODIFY <object> <property>=<value>` - Customize creations

### Advanced Intelligence
- `LIST [objects|skills|agents]` - Discover available resources
- `IF <condition> THEN <action>` - Conditional logic preventing waste
- `DEFINE <verb> AS <template>` - Create custom family workflows
- `INSPECT <object>` - Detailed examination and learning

## Multi-Generational Family System 👨‍👩‍👧‍👦

### Family Dynamics
- **Early Breeding**: Families form after tick 20-30 when basic infrastructure exists
- **Child Inheritance**: Children inherit combined traits, average temperature, and parent knowledge
- **Active Participation**: New family members immediately contribute to civilization
- **Growing Population**: Each generation brings fresh perspectives and capabilities

### Example Family Evolution
```
Tick 14: Eve → BREED WITH Adam
Tick 15: Adam → BREED WITH Eve
Result: child_15_Eve_Ada_be9f spawned with combined traits

Family Statistics:
- Parents: Adam (builder) + Eve (explorer) 
- Child: Inherited systematic + creative traits
- Knowledge Transfer: Tool-making, exploration, building skills
- Population Growth: 2 → 3 active participants
```

## Discovery Materials System 🔮

### Enhancement Features
- **Cosmic Materials**: Crystal shards, ancient gears, energy cores with `energy_level=high`
- **Enhanced Experiments**: Discovery materials create objects with `enhanced=true` properties
- **Special Properties**: Enhanced objects get `discovery_level`, `rarity=enhanced` attributes
- **Environmental Spawning**: Discovery caches and innovation surges create legendary materials

### Example Enhanced Objects
```json
"enhanced_6185": {
  "creator": "Adam",
  "discovered_using": ["crystal_shard", "water"],
  "enhanced": true,
  "discovery_level": 1,
  "rarity": "enhanced"
}
```

## Environmental Dynamics System

### 🌡️ Dynamic Weather & Seasons
- **4 Seasons**: Spring, Summer, Autumn, Winter (25 ticks each)
- **Weather Patterns**: Clear, cloudy, rainy, windy conditions
- **Seasonal Adaptation**: Families adjust strategies to environmental conditions

### ⚡ Environmental Events (9 Types)
- **Discovery Caches**: Spawn legendary materials (crystal_shard, ancient_gear, energy_core)
- **Innovation Surges**: Boost creativity and combination success (4-tick duration)
- **Storms**: Damage exposed objects, encourage family shelter-building
- **Resource Scarcity**: Drive cooperation and resource sharing between generations
- **Tool Wear**: Promote maintenance and repair skills across the family

### 📈 Resource Management
- **Dynamic Resources**: Wood, stone, water, food with regeneration/depletion
- **Scarcity Pressure**: Encourages trading and efficient resource use within families
- **Discovery Materials**: Special cosmic/ancient items for breakthrough experimentation

## Innovation Reward System

### 🎯 Adaptive World Focus
Rotates every 15 ticks to prevent stagnation:
- **EXPLORATION**: Discover new locations and resources
- **SURVIVAL**: Build shelter, manage resources, prepare for challenges  
- **INNOVATION**: Experiment, combine objects, create new technologies
- **COOPERATION**: Teach skills, trade resources, build families

### 🏆 Innovation Rewards
- **COMBINE**: Combination rewards (wooden_beam + rope → reinforced_beam)
- **EXPERIMENT**: Experimentation rewards (crystal_shard + water → enhanced discoveries)
- **DEFINE**: Custom workflow rewards, trigger innovation surges
- **TRADE**: Resource sharing rewards, reduce scarcity pressure

## Anti-Loop Intelligence

### 🔄 Smart Loop Detection
- **Action History Tracking**: Monitors last 10 agent actions
- **Pattern Recognition**: Detects repetitive unsuccessful behaviors  
- **Creation-Focused Alternatives**: Forces CREATE commands when stuck in ANALYZE loops
- **Discovery Priority**: Suggests discovery material combinations when available
- **Anti-Duplication**: Warns at 2 duplicates, blocks creation at 3+ identical objects

### 🧠 Enhanced Agent Intelligence
- **Environmental Awareness**: Agents respond to weather, seasons, events
- **Discovery Material Priority**: Explicit instructions to use cosmic/ancient materials
- **Family Strategy**: Multi-generational planning and resource sharing
- **Contextual Adaptation**: Behavior based on world focus and family needs

## Live Dashboard

```powershell
streamlit run dashboards/world_view.py
```

The dashboard provides real-time civilization tracking:
- **Family Trees**: Multi-generational relationships and inheritance
- **Innovation Metrics**: Object creation tracking, innovation rewards
- **Discovery Tracking**: Enhanced objects with special properties
- **Environmental State**: Current season, weather, active events
- **Population Growth**: Family expansion and skill distribution

## Example Genesis Progression

Watch civilization emerge from nothing through family cooperation:

```
🌍 Genesis Day 1: Empty world | 🎯 Focus: SURVIVAL
[world] Eve created hammer (basic survival tools)
[world] Adam created shelter (protection established)

🌍 Genesis Day 15: Family Formation | 🎯 Focus: COOPERATION  
[world] Eve asked to breed with Adam
[world] Adam asked to breed with Eve
[breeding] 🍼 Spawned child_15_Eve_Ada_be9f from Eve+Adam

🌍 Genesis Day 25: Multi-Generational Society | 🎯 Focus: INNOVATION
[world] child_15_Eve_Ada_be9f gathered water (contributing to family)
[world] Eve combined berries and water into refreshing_drink
🎉 INNOVATION REWARD: Eve gained 3 innovation points for COMBINE!

Population: 2 → 3 active family members
Civilization Level: Survival → Family → Innovation
```

## Key Features Achieved ✅

✅ **Multi-Generational Families**: Successful breeding with active child participation  
✅ **Discovery Materials Working**: Crystal shards, ancient gears creating enhanced objects  
✅ **Environmental Events**: Dynamic world with discovery caches, innovation surges  
✅ **Innovation Rewards**: Rewards for creative combinations and experiments  
✅ **Enhanced Experiments**: Special properties on discovery-based objects  
✅ **Family Skill Sharing**: Knowledge transfer between generations  
✅ **No Stuck Loops**: Continuous innovation throughout civilization growth  
✅ **Advanced Combinations**: wooden_beam + rope → reinforced_beam  
✅ **Perfect Command Syntax**: 100% WORLD: directive compliance

## Future Civilization Features

- 🏘️ **Village Building**: Multi-family settlements and trade networks
- 📚 **Cultural Evolution**: Knowledge preservation across generations  
- 🎓 **Specialization**: Family members developing unique roles and expertise
- 🌐 **Inter-Family Dynamics**: Trade, cooperation, and competition between families
- 📊 **Civilization Metrics**: Cultural complexity, technological advancement tracking
- 🎮 **Interactive Mode**: Human-guided civilization development

## Contributing

Genesis Agents demonstrates the emergence of artificial civilizations. Contributions welcome for:

- Multi-family interaction systems and tribal dynamics
- Advanced inheritance mechanisms and genetic programming
- Economic systems and inter-generational resource management
- Cultural evolution tracking and knowledge preservation
- Village and settlement building mechanics

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 