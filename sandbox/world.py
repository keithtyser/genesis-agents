from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict
import json, os, tempfile
from uuid import uuid4
from datetime import datetime


@dataclass
class WorldState:
    tick: int = 0
    objects: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    agents: Dict[str, Dict[str, Any]]  = field(default_factory=dict)

    # -------------------------------------------------------------- #
    def add_object(self, kind: str, props: Dict[str, Any] | None = None) -> str:
        """
        Add an object of given kind; return its 8-char uuid.
        """
        oid = uuid4().hex[:8]
        self.objects[oid] = {"kind": kind, **(props or {})}
        return oid

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
        return cls(
            tick=data.get("tick", 0),
            objects=data.get("objects", {}),
            agents=data.get("agents", {}),
        ) 