import json, pathlib, glob, os

WORLD_PATH = pathlib.Path(os.getenv("WORLD_PATH", "world.json"))
LOG_DIR    = pathlib.Path("logs")

def load_world():
    try:
        return json.loads(WORLD_PATH.read_text())
    except FileNotFoundError:
        return {"tick": 0, "agents": {}, "objects": {}}

def tail_logs(max_lines: int = 100):
    """Return a list of recent log records from the newest run_*.jsonl file."""
    try:
        log_files = sorted(LOG_DIR.glob("run_*.jsonl"),
                           key=lambda p: p.stat().st_mtime,
                           reverse=True)
        if not log_files:
            return []
        path = log_files[0]
        with path.open("r", encoding="utf-8") as f:
            lines = f.readlines()[-max_lines:]
        recs = []
        for line in lines:
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return recs
    except Exception:
        return [] 