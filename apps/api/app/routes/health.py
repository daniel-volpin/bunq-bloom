from fastapi import APIRouter

from app.settings import get_settings

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "integrations": {
            "claude": "fake" if settings.use_fake_ai else "not_configured",
            "bunq": "fake" if settings.use_fake_bunq else "not_configured",
            "state": "ok",
        },
    }

