import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from app.models.domain import seed_state


class StateRepository:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            state = seed_state()
            self.save(state)
            return deepcopy(state)

        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, state: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        tmp_path.replace(self.path)

    def reset(self) -> dict[str, Any]:
        state = seed_state()
        self.save(state)
        return deepcopy(state)

