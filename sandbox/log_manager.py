from __future__ import annotations
from pathlib import Path
import json, datetime as dt, shutil, os

ROTATE_DAYS = 7

class LogManager:
    def __init__(self, base: str = "logs"):
        self.base = Path(base)
        self.base.mkdir(exist_ok=True)
        (self.base / "archive").mkdir(exist_ok=True)
        self._rotate_old()

        ts   = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = self.base / f"run_{ts}.jsonl"
        self._fh  = self.path.open("a", encoding="utf-8")

    # -------------------------------------------------------------- #
    def write(self, rec: dict):
        """Append a JSON record + newline."""
        json.dump(rec, self._fh, ensure_ascii=False)
        self._fh.write("\n")
        self._fh.flush()

    # -------------------------------------------------------------- #
    def close(self):
        self._fh.close()

    # -------------------------------------------------------------- #
    def _rotate_old(self):
        cutoff = dt.datetime.now() - dt.timedelta(days=ROTATE_DAYS)
        for f in self.base.glob("run_*.jsonl"):
            ts_str = f.stem.split("_", 1)[1]
            try:
                ts = dt.datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
            except ValueError:
                continue
            if ts < cutoff:
                shutil.move(str(f), self.base / "archive" / f.name) 