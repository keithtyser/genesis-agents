# Enhanced Empty-Earth Sandbox

![python](https://img.shields.io/badge/Python-3.11+-blue)
![license](https://img.shields.io/badge/License-MIT-green)
![agents](https://img.shields.io/badge/Agents-Adam%20%26%20Eve-purple)
![commands](https://img.shields.io/badge/Commands-15%2B%20Enhanced-orange)

## What's New 🚀

The **Enhanced Empty-Earth Sandbox** is a comprehensive AI simulation platform featuring intelligent LLM agents (Adam & Eve) in a dynamic world with:

- **🌍 Environmental Dynamics**: Seasons, weather, random events, resource management
- **🧠 Advanced Agent Intelligence**: 15+ sophisticated commands, loop detection, adaptive behavior
- **⚡ Innovation System**: Rewards for creativity, discovery materials, experimentation
- **🔄 Anti-Loop Technology**: Smart detection and alternative goal injection
- **📊 191% Performance Improvement**: From 0.06 to 0.175 objects/tick innovation rate

## Why

Empty-Earth Sandbox simulates emergent behaviors in a virtual world where AI agents don't just chat—they **build, explore, innovate, and cooperate**. Watch Adam and Eve evolve from basic survival to complex civilizations through environmental pressures, seasonal changes, and creative challenges.

## Quick Start

```powershell
git clone https://github.com/keithtyser/sandbox-ai.git
cd sandbox-ai
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:OPENAI_API_KEY="sk-..."  # set your key
python -m cli.sandbox --ticks 50
```

## Enhanced Command System

Agents now have access to **15+ sophisticated commands** (expanded from 4 basic verbs):

### Basic Actions
- `CREATE <object>` - Build tools, shelter, resources
- `MOVE TO <location>` - Explore different environments
- `SET <property>=<value>` - Configure agent properties

### Social & Learning
- `TEACH <agent> <skill>` - Share knowledge and abilities
- `LEARN <skill> [FROM <agent>]` - Acquire new capabilities
- `TRADE <item> FOR <item> WITH <agent>` - Economic cooperation

### Innovation & Discovery
- `COMBINE <obj1> AND <obj2> [INTO <result>]` - Create advanced objects
- `EXPERIMENT WITH <materials...>` - Discover new possibilities
- `ANALYZE <object>` - Gain detailed knowledge
- `USE <object> [ON <target>]` - Apply tools effectively
- `MODIFY <object> <property>=<value>` - Customize creations

### Advanced Features
- `LIST [objects|skills|agents]` - Discover available resources
- `IF <condition> THEN <action>` - Conditional logic
- `DEFINE <verb> AS <template>` - Create custom workflows
- `INSPECT <object>` - Detailed examination

## Environmental Dynamics System

### 🌡️ Dynamic Weather & Seasons
- **4 Seasons**: Spring, Summer, Autumn, Winter (25 ticks each)
- **Weather Patterns**: Clear, cloudy, rainy, windy conditions
- **Seasonal Adaptation**: Agents adjust strategies to environmental conditions

### ⚡ Environmental Events (9 Types)
- **Storms**: Damage exposed objects, encourage shelter-building
- **Resource Abundance/Scarcity**: Drive cooperation and resource management
- **Innovation Surges**: Boost creativity and combination success
- **Discovery Caches**: Introduce rare materials for experimentation
- **Tool Wear**: Promote maintenance and repair skills

### 📈 Resource Management
- **Dynamic Resources**: Wood, stone, water, food with regeneration/depletion
- **Scarcity Pressure**: Encourages trading and efficient resource use
- **Discovery Materials**: Special items for advanced experimentation

## Innovation Reward System

### 🎯 Adaptive World Focus
Rotates every 15 ticks to prevent stagnation:
- **EXPLORATION**: Discover new locations and resources
- **SURVIVAL**: Build shelter, manage resources, prepare for challenges
- **INNOVATION**: Experiment, combine objects, create new technologies
- **COOPERATION**: Teach skills, trade resources, build together

### 🏆 Innovation Rewards
- **COMBINE**: +3 points, unlock crystal shards
- **EXPERIMENT**: +5 points, generate rare materials
- **DEFINE**: +4 points, trigger innovation surges
- **TRADE**: +2 points, reduce scarcity pressure

## Anti-Loop Intelligence

### 🔄 Smart Loop Detection
- **Action History Tracking**: Monitors last 10 agent actions
- **Pattern Recognition**: Detects repetitive unsuccessful behaviors
- **Alternative Goal Injection**: Suggests new directions when stuck

### 🧠 Enhanced Agent Prompts
- **Environmental Awareness**: Agents respond to weather, seasons, events
- **Contextual Strategy**: Adaptive behavior based on world focus and conditions
- **Loop Breaking**: Explicit instructions to try new approaches when stuck

## Live Dashboard

```powershell
streamlit run dashboards/world_view.py
```

The dashboard provides real-time visualization including:
- **Gini Coefficient**: Object ownership distribution (0 = equality, 1 = monopoly)
- **Innovation Metrics**: Object creation rate, skill development, discoveries
- **Environmental State**: Current season, weather, active events
- **Agent Progress**: Skills learned, objects created, cooperation events

## Performance Metrics

### 📊 Before vs After Enhancement

| Metric | Baseline | Enhanced | Improvement |
|--------|----------|----------|-------------|
| Innovation Rate | 0.06 objects/tick | 0.175 objects/tick | **+191%** |
| Stuck Loop Issue | After tick 10 | Eliminated | **✅ Fixed** |
| Command Variety | 4 basic verbs | 15+ advanced commands | **+275%** |
| Environmental Events | None | 9 dynamic types | **✅ New** |
| Agent Intelligence | Basic | Adaptive & Context-aware | **✅ Enhanced** |

## Testing & Development Tools

### 🧪 Test Scripts
- `test_enhanced_commands.py` - Verify all 15+ commands work
- `test_complete_enhancements.py` - Full system integration test
- `debug_agent_output.py` - Debug agent responses and commands
- `test_final_improvements.py` - LIST command and discovery features

### 📝 Sample Test Run
```powershell
python test_complete_enhancements.py
# Expected: 7+ objects in 40 ticks, no loops, environmental adaptation
```

## Folder Map

```text
│  README.md
│  world.json
│  memory.py
│  test_enhanced_commands.py          # Command system tests
│  test_complete_enhancements.py      # Full integration tests  
│  debug_agent_output.py             # Debug tools
│  test_final_improvements.py        # Discovery feature tests
├─sandbox/
│   ├─agent.py                       # Enhanced agent intelligence
│   ├─breeding.py
│   ├─bus.py
│   ├─commands.py                    # 15+ enhanced commands
│   ├─config.py
│   ├─context.py
│   ├─llm.py
│   ├─log_manager.py
│   ├─memory_manager.py
│   ├─scheduler.py                   # Environmental dynamics & focus rotation
│   ├─summary.py
│   ├─world.py                       # Enhanced with environment system
├─experiments/
│   ├─encryption.py
│   └─code_review.py
├─dashboards/
│   ├─world_view.py
│   ├─graph_builder.py
│   ├─utils.py
├─cli/
│   ├─sandbox.py
```

## Environment Variables

| Variable Name          | Description                          | Default Value |
|------------------------|--------------------------------------|---------------|
| `OPENAI_API_KEY`       | Your OpenAI API key for LLM access   | None          |
| `MAX_AGENTS`           | Maximum number of agents in the sim  | 10            |
| `MAX_PROMPT_TOKENS`    | Token limit per prompt               | 12000         |
| `OPENAI_PARALLEL_MAX`  | Max parallel API calls to OpenAI     | 5             |
| `SAVE_EVERY`           | Save world state every N ticks       | 10            |
| `SNAP_EVERY`           | Create snapshots every N ticks       | 500           |

## Common Commands

- **Run enhanced simulation**:
  ```powershell
  python -m cli.sandbox --ticks 100
  ```
- **Test all enhancements**:
  ```powershell
  python test_complete_enhancements.py
  ```
- **Debug agent behavior**:
  ```powershell
  python debug_agent_output.py
  ```
- **View logs tail**:
  ```powershell
  Get-Content -Path logs\latest.log -Tail 50
  ```

## Example Enhanced Gameplay

Watch Adam and Eve demonstrate sophisticated behaviors:

```
🌍 Environment: clear weather, spring season | 🎯 Focus: EXPLORATION
[world] Eve self-learned tool-making
[environment] 🌍 ENVIRONMENTAL EVENT: Tools show signs of wear (lasts 1 ticks)
[world] Adam created learning_materials (id=a3ca4199)
[world] Eve moved to forest
[world] Adam combined wood AND stone INTO advanced_tool (id=5bf4e1f2)
🎉 INNOVATION REWARD: Adam gained 3 innovation points for COMBINE!
[system] 🎯 World focus shifted to: SURVIVAL
[world] Eve created shelter
[environment] 🌍 ENVIRONMENTAL EVENT: Storm damages exposed objects (lasts 3 ticks)
[world] Adam taught tool-making to Eve
[world] Eve experimented with wood stone and discovered experimental_fire (id=7ab2c8d9)
🎉 INNOVATION REWARD: Eve gained 5 innovation points for EXPERIMENT!
```

## Key Features Demonstrated

✅ **Environmental Adaptation**: Agents respond to storms by building shelter  
✅ **Innovation Rewards**: COMBINE and EXPERIMENT actions yield bonuses  
✅ **Knowledge Sharing**: Teaching and learning between agents  
✅ **Discovery System**: Experimentation leads to new objects  
✅ **Focus Adaptation**: Behavior changes based on world priorities  
✅ **No Stuck Loops**: Agents continue innovating throughout simulation  

## Known Limitations / Future Roadmap

- 🔄 Breeding system needs refinement for complex family trees
- 💰 Dynamic cost optimization for longer simulations  
- 🧠 Memory system could benefit from embeddings-based recall
- 🏗️ Multi-agent infrastructure projects (villages, trade networks)
- 🎮 Interactive mode for human-agent collaboration
- 📊 Advanced metrics dashboard with social network analysis

## Contributing

The Enhanced Empty-Earth Sandbox demonstrates significant advances in AI agent simulation. Contributions welcome for:

- New environmental event types
- Advanced agent cooperation mechanisms  
- Multi-generational family dynamics
- Economic system enhancements
- Cultural evolution tracking

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 