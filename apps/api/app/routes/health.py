from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter

from app.settings import get_settings

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health() -> dict:
    settings = get_settings()
    claude = _integration_status(settings.claude_mode(), settings.claude_missing_config_codes())
    bunq = _integration_status(settings.bunq_mode(), settings.bunq_missing_config_codes())
    state = _state_status(settings.state_path)
    uploads = _directory_status(settings.upload_dir, "upload_dir")
    readiness_status = "ready" if _all_ok(claude, bunq, state, uploads) else "not_ready"

    return {
        "status": "ok",
        "readiness_status": readiness_status,
        "integrations": {
            "claude": claude,
            "bunq": bunq,
            "state": state,
            "uploads": uploads,
        },
    }


def _integration_status(mode: str, missing_config: list[str]) -> dict:
    return {
        "mode": mode,
        "status": "configured" if not missing_config else "not_configured",
        "missing_config": missing_config,
    }


def _state_status(state_path: Path) -> dict:
    parent_status = _directory_status(state_path.parent, "state_path_parent")
    missing_config = list(parent_status["missing_config"])
    status = parent_status["status"]

    if status == "ok" and state_path.exists() and not state_path.is_file():
        status = "not_ready"
        missing_config.append("state_path_not_file")

    return {
        "status": status,
        "path_parent": parent_status,
        "missing_config": missing_config,
    }


def _directory_status(path: Path, code_prefix: str) -> dict:
    if not path.exists():
        creatable = _missing_path_is_creatable(path)
        return {
            "status": "ok" if creatable else "not_ready",
            "exists": False,
            "readable": False,
            "writable": creatable,
            "creatable": creatable,
            "missing_config": [] if creatable else [f"{code_prefix}_missing"],
        }

    if not path.is_dir():
        return {
            "status": "not_ready",
            "exists": True,
            "readable": False,
            "writable": False,
            "creatable": False,
            "missing_config": [f"{code_prefix}_not_directory"],
        }

    readable = _can_iterate(path)
    writable = _can_write_and_read(path)
    missing_config = []
    if not readable:
        missing_config.append(f"{code_prefix}_not_readable")
    if not writable:
        missing_config.append(f"{code_prefix}_not_writable")

    return {
        "status": "ok" if readable and writable else "not_ready",
        "exists": True,
        "readable": readable,
        "writable": writable,
        "creatable": True,
        "missing_config": missing_config,
    }


def _can_iterate(path: Path) -> bool:
    try:
        next(path.iterdir(), None)
        return True
    except OSError:
        return False


def _can_write_and_read(path: Path) -> bool:
    probe_path = path / f".bloom-health-{uuid4().hex}.tmp"
    try:
        probe_path.write_text("ok", encoding="utf-8")
        return probe_path.read_text(encoding="utf-8") == "ok"
    except OSError:
        return False
    finally:
        try:
            probe_path.unlink()
        except OSError:
            pass


def _missing_path_is_creatable(path: Path) -> bool:
    existing_parent = path.parent
    while not existing_parent.exists() and existing_parent != existing_parent.parent:
        existing_parent = existing_parent.parent
    if not existing_parent.exists() or not existing_parent.is_dir():
        return False
    return _can_write_and_read(existing_parent)


def _all_ok(*checks: dict) -> bool:
    return all(check["status"] == "ok" or check["status"] == "configured" for check in checks)
