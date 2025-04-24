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
        """
        def _dt_handler(o):
            if isinstance(o, datetime):
                return o.isoformat()
            raise TypeError

        data = asdict(self)
        json_str = json.dumps(data, indent=2, default=_dt_handler)

        dir_ = os.path.dirname(path) or "."
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False, dir=dir_
        ) as tmp:
            tmp.write(json_str)
            tmp_path = tmp.name
        os.replace(tmp_path, path)

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