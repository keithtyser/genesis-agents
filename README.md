# Enhanced Empty-Earth Sandbox

![python](https://img.shields.io/badge/Python-3.11+-blue)
![license](https://img.shields.io/badge/License-MIT-green)
![agents](https://img.shields.io/badge/Agents-Adam%20%26%20Eve-purple)
![commands](https://img.shields.io/badge/Commands-15%2B%20Enhanced-orange)

## What's New 🚀

The **Enhanced Empty-Earth Sandbox** is a comprehensive AI simulation platform featuring intelligent LLM agents (Adam & Eve) in a dynamic world with:

- **⚡ Enhanced Discovery Materials**: Crystal shards, ancient gears, energy cores creating breakthrough innovations
- **🧪 Advanced Experimentation**: Discovery materials enable enhanced objects with special properties
- **🌍 Environmental Dynamics**: Seasons, weather, discovery caches
- **🔄 Anti-Loop Technology**: Eliminated analysis paralysis - agents now create continuously
- **🏆 Innovation Rewards System**: Rewards for creativity and breakthrough discoveries
- **🧠 Smart Agent Intelligence**: Context-aware behavior, discovery material prioritization

## Why

Empty-Earth Sandbox simulates emergent behaviors in a virtual world where AI agents don't just chat—they **build, explore, innovate, and cooperate**. Watch Adam and Eve evolve from basic survival to complex civilizations through environmental pressures, seasonal changes, and creative challenges.

Agents now create sophisticated object progressions: basic tools → advanced combinations → enhanced discoveries using mysterious materials.

## Quick Start

```powershell
git clone https://github.com/keithtyser/sandbox-ai.git
cd sandbox-ai
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:OPENAI_API_KEY="sk-..."  # set your key
python fresh_start.py         # Fresh simulation with all enhancements
```

## Enhanced Command System

Agents now have access to **15+ sophisticated commands** with anti-duplication logic and discovery material prioritization:

### Basic Actions
- `CREATE <object>` - Build tools, shelter, resources (with duplicate detection)
- `MOVE TO <location>` - Explore different environments
- `SET <property>=<value>` - Configure agent properties

### Social & Learning
- `TEACH <agent> <skill>` - Share knowledge and abilities
- `LEARN <skill> [FROM <agent>]` - Acquire new capabilities
- `TRADE <item> FOR <item> WITH <agent>` - Economic cooperation

### Innovation & Discovery
- `COMBINE <obj1> AND <obj2> [INTO <result>]` - Create advanced objects
- `EXPERIMENT WITH <materials...>` - Enhanced with discovery materials
- `ANALYZE <object>` - Gain detailed knowledge
- `USE <object> [ON <target>]` - Apply tools effectively
- `MODIFY <object> <property>=<value>` - Customize creations

### Advanced Features
- `LIST [objects|skills|agents]` - Discover available resources
- `IF <condition> THEN <action>` - Conditional logic with smart creation prevention
- `DEFINE <verb> AS <template>` - Create custom workflows
- `INSPECT <object>` - Detailed examination

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
- **Seasonal Adaptation**: Agents adjust strategies to environmental conditions

### ⚡ Environmental Events (9 Types)
- **Discovery Caches**: Spawn legendary materials (crystal_shard, ancient_gear, energy_core)
- **Innovation Surges**: Boost creativity and combination success (4-tick duration)
- **Storms**: Damage exposed objects, encourage shelter-building
- **Resource Scarcity**: Drive cooperation and resource management
- **Tool Wear**: Promote maintenance and repair skills

### 📈 Resource Management
- **Dynamic Resources**: Wood, stone, water, food with regeneration/depletion
- **Scarcity Pressure**: Encourages trading and efficient resource use
- **Discovery Materials**: Special cosmic/ancient items for breakthrough experimentation

## Innovation Reward System

### 🎯 Adaptive World Focus
Rotates every 15 ticks to prevent stagnation:
- **EXPLORATION**: Discover new locations and resources
- **SURVIVAL**: Build shelter, manage resources, prepare for challenges  
- **INNOVATION**: Experiment, combine objects, create new technologies
- **COOPERATION**: Teach skills, trade resources, build together

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

### 🧠 Enhanced Agent Prompts
- **Environmental Awareness**: Agents respond to weather, seasons, events
- **Discovery Material Priority**: Explicit instructions to use cosmic/ancient materials
- **Contextual Strategy**: Adaptive behavior based on world focus and conditions
- **Loop Breaking**: Explicit instructions to try new approaches when stuck

## Live Dashboard

```powershell
streamlit run dashboards/world_view.py
```

The dashboard provides real-time visualization including:
- **Innovation Metrics**: Object creation tracking, innovation rewards
- **Discovery Tracking**: Enhanced objects with special properties
- **Environmental State**: Current season, weather, active events
- **Agent Progress**: Skills learned, objects created, cooperation events

## Example Enhanced Gameplay

Watch Adam and Eve demonstrate sophisticated behaviors with discovery materials:

```
🌍 Environment: clear weather, spring season | 🎯 Focus: EXPLORATION
[world] Eve self-learned tool-making
[world] Adam created shelter (id=6c6bccfe)
[world] Adam combined axe and wood into wooden_beam (id=56a2d521)
🎉 INNOVATION REWARD: Adam gained 3 innovation points for COMBINE!

🌍 ENVIRONMENTAL EVENT: Ancient cache of mysterious objects discovered
[world] Discovery materials added: crystal_shard, ancient_gear, energy_core

[world] Adam analyzed crystal_shard: Object crystal_shard: kind=crystal_shard, creator=cosmic, properties=7
[world] Adam experimented with crystal_shard, water and discovered enhanced_6185 (id=6d57b3d1) - Enhanced by discovery materials!
🎉 INNOVATION REWARD: Adam gained 5 innovation points for EXPERIMENT!

Enhanced Object Properties:
{
  "enhanced": true,
  "discovery_level": 1, 
  "rarity": "enhanced"
}
```

## Key Features Demonstrated ✅

✅ **Discovery Materials Working**: Crystal shards, ancient gears creating enhanced objects  
✅ **Environmental Events**: Events including discovery caches, innovation surges  
✅ **Innovation Rewards**: Rewards for creative combinations and experiments  
✅ **Enhanced Experiments**: Special properties on discovery-based objects  
✅ **Skills Progression**: Both agents learning complementary skills  
✅ **No Stuck Loops**: Continuous innovation throughout simulation  
✅ **Advanced Combinations**: wooden_beam + rope → reinforced_beam  
✅ **Anti-Duplication Logic**: Smart warnings prevent excessive repetition  

## Known Limitations / Future Roadmap

- 🔄 Breeding system needs refinement for complex family trees
- 💰 Dynamic cost optimization for longer simulations  
- 🧠 Memory system could benefit from embeddings-based recall
- 🏗️ Multi-agent infrastructure projects (villages, trade networks)
- 🎮 Interactive mode for human-agent collaboration
- 📊 Advanced metrics dashboard with social network analysis

## Contributing

The Enhanced Empty-Earth Sandbox demonstrates advances in AI agent simulation. Contributions welcome for:

- New discovery material types and enhanced object properties
- Advanced agent cooperation mechanisms using cosmic materials
- Multi-generational family dynamics with enhanced inheritance
- Economic system enhancements leveraging discovery rewards
- Cultural evolution tracking through innovation metrics

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 