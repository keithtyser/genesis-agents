# Empty-Earth Sandbox

![python](https://img.shields.io/badge/Python-3.11+-blue)
![license](https://img.shields.io/badge/License-MIT-green)

## Why

Empty-Earth Sandbox is an experimental platform to simulate emergent behaviors in a virtual world driven by multiple LLM agents. These agents interact, evolve, and shape their environment through plug-in micro-experiments. A Streamlit dashboard provides real-time visualization of the world's dynamics, including metrics like object ownership distribution.

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

## Live Dashboard

```powershell
streamlit run dashboards/world_view.py
```

The dashboard computes a **Gini coefficient** of object ownership — 0 = perfect equality, 1 = total monopoly.

## Folder Map

```text
│  README.md
│  world.json
│  memory.py
├─sandbox/
│   ├─agent.py
│   ├─breeding.py
│   ├─bus.py
│   ├─commands.py
│   ├─config.py
│   ├─context.py
│   ├─llm.py
│   ├─log_manager.py
│   ├─memory_manager.py
│   ├─scheduler.py
│   ├─summary.py
│   ├─world.py
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

## Common Commands

- **Run 1,000 ticks**:
  ```powershell
  python -m cli.sandbox --ticks 1000
  ```
- **View logs tail**:
  ```powershell
  Get-Content -Path logs\latest.log -Tail 50
  ```

## Known Limitations / Roadmap

- Breeding cooldown mechanism is rudimentary
- Non-deterministic costs per run
- Token truncation may cut context
- No GPU support yet

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 