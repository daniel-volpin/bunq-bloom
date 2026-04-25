from fastapi import APIRouter, Depends

from app.dependencies import get_gig_service
from app.models.api import BalanceResponse
from app.services.gig_service import GigService

router = APIRouter(tags=["balance"])


@router.get("/api/balance/kid", response_model=BalanceResponse)
def get_kid_balance(service: GigService = Depends(get_gig_service)) -> dict:
    return service.get_kid_balance()
