from fastapi import APIRouter, Depends

from app.dependencies import get_gig_service
from app.models.api import (
    BeforePhotoRequest,
    CompleteGigRequest,
    CompleteGigResponse,
    GigCreateRequest,
    GigEnvelopeResponse,
    ListGigsResponse,
    RetryPaymentRequest,
)
from app.services.gig_service import GigService

router = APIRouter(prefix="/api/gigs", tags=["gigs"])


@router.get("", response_model=ListGigsResponse)
def list_gigs(service: GigService = Depends(get_gig_service)) -> dict:
    return service.list_gigs()


@router.post("", response_model=GigEnvelopeResponse)
def create_gig(payload: GigCreateRequest, service: GigService = Depends(get_gig_service)) -> dict:
    return service.create_gig(payload)


@router.post("/{gig_id}/claim", response_model=GigEnvelopeResponse)
def claim_gig(gig_id: str, service: GigService = Depends(get_gig_service)) -> dict:
    return service.claim_gig(gig_id)


@router.post("/{gig_id}/before-photo", response_model=GigEnvelopeResponse)
def add_before_photo(
    gig_id: str,
    payload: BeforePhotoRequest,
    service: GigService = Depends(get_gig_service),
) -> dict:
    return service.add_before_photo(gig_id, payload.image_base64)


@router.post("/{gig_id}/complete", response_model=CompleteGigResponse)
def complete_gig(
    gig_id: str,
    payload: CompleteGigRequest,
    service: GigService = Depends(get_gig_service),
) -> dict:
    return service.complete_gig(
        gig_id,
        after_image_base64=payload.after_image_base64,
        idempotency_key=payload.idempotency_key,
    )


@router.post("/{gig_id}/retry-payment", response_model=CompleteGigResponse)
def retry_payment(
    gig_id: str,
    payload: RetryPaymentRequest,
    service: GigService = Depends(get_gig_service),
) -> dict:
    return service.retry_payment(gig_id, idempotency_key=payload.idempotency_key)
