import json, pathlib, glob, os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

WORLD_PATH = pathlib.Path(os.getenv("WORLD_PATH", "world.json"))
LOG_DIR    = pathlib.Path("logs")

class LogFileWatcher(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback
        self.last_position = 0
        self.current_file = None

    def on_modified(self, event):
        if event.is_directory:
            return
        log_file = pathlib.Path(event.src_path)
        if log_file.suffix != '.jsonl' or not log_file.name.startswith('run_'):
            return
        if self.current_file != log_file:
            self.current_file = log_file
            self.last_position = log_file.stat().st_size
        with log_file.open('r', encoding='utf-8') as f:
            f.seek(self.last_position)
            new_lines = f.readlines()
            self.last_position = f.tell()
            for line in new_lines:
                try:
                    record = json.loads(line)
                    self.callback(record)
                except json.JSONDecodeError:
                    continue

def stream_logs(callback):
    """Stream new log records from the newest run_*.jsonl file as they are written.
    
    Args:
        callback: A function to call with each new log record.
    
    Returns:
        An observer object. Call observer.start() to begin watching, and observer.stop() to stop.
    """
    event_handler = LogFileWatcher(callback)
    observer = Observer()
    observer.schedule(event_handler, str(LOG_DIR), recursive=False)
    return observer

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