from fastapi import APIRouter, Depends

from app.dependencies import get_snap_and_learn_service
from app.models.api import SnapAndLearnRequest, SnapAndLearnResponse
from app.services.snap_and_learn_service import SnapAndLearnService

router = APIRouter(prefix="/api/snap-and-learn", tags=["snap-and-learn"])


@router.post("/analyze", response_model=SnapAndLearnResponse)
def analyze_snap(
    payload: SnapAndLearnRequest,
    service: SnapAndLearnService = Depends(get_snap_and_learn_service),
) -> SnapAndLearnResponse:
    return service.analyze(payload.image_base64)