import json
from collections.abc import Iterator
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback.
    fcntl = None

from app.models.domain import seed_state


_LOCKS_GUARD = RLock()
_PROCESS_LOCKS: dict[Path, RLock] = {}


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
        tmp_path = self.path.with_name(f".{self.path.name}.{uuid4().hex}.tmp")
        try:
            with tmp_path.open("w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
            tmp_path.replace(self.path)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    @contextmanager
    def transaction(self) -> Iterator[dict[str, Any]]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        process_lock = self._process_lock()
        with process_lock:
            with self._file_lock():
                state = self.load()
                yield state
                self.save(state)

    def reset(self) -> dict[str, Any]:
        state = seed_state()
        self.save(state)
        return deepcopy(state)

    def _process_lock(self) -> RLock:
        key = self.path.resolve()
        with _LOCKS_GUARD:
            if key not in _PROCESS_LOCKS:
                _PROCESS_LOCKS[key] = RLock()
            return _PROCESS_LOCKS[key]

    @contextmanager
    def _file_lock(self) -> Iterator[None]:
        lock_path = self.path.with_suffix(f"{self.path.suffix}.lock")
        with lock_path.open("a+", encoding="utf-8") as lock_file:
            if fcntl is not None:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                if fcntl is not None:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
