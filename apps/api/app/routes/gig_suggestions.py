from fastapi import APIRouter, Depends

from app.dependencies import get_gig_suggestion_service
from app.models.api import (
    ApproveGigSuggestionResponse,
    CreateGigSuggestionRequest,
    GigSuggestionEnvelopeResponse,
    KidNotificationEnvelopeResponse,
    ListGigSuggestionsResponse,
    ListKidNotificationsResponse,
)
from app.services.gig_suggestion_service import GigSuggestionService

router = APIRouter(tags=["gig suggestions"])


@router.get("/api/gig-suggestions", response_model=ListGigSuggestionsResponse)
def list_suggestions(service: GigSuggestionService = Depends(get_gig_suggestion_service)) -> dict:
    return service.list_suggestions()


@router.post("/api/gig-suggestions", response_model=GigSuggestionEnvelopeResponse)
def create_suggestion(
    payload: CreateGigSuggestionRequest,
    service: GigSuggestionService = Depends(get_gig_suggestion_service),
) -> dict:
    return service.create_suggestion(payload)


@router.post("/api/gig-suggestions/{suggestion_id}/approve", response_model=ApproveGigSuggestionResponse)
def approve_suggestion(
    suggestion_id: str,
    service: GigSuggestionService = Depends(get_gig_suggestion_service),
) -> dict:
    return service.approve_suggestion(suggestion_id)


@router.get("/api/notifications/kid", response_model=ListKidNotificationsResponse)
def list_kid_notifications(service: GigSuggestionService = Depends(get_gig_suggestion_service)) -> dict:
    return service.list_kid_notifications()


@router.post("/api/notifications/{notification_id}/dismiss", response_model=KidNotificationEnvelopeResponse)
def dismiss_kid_notification(
    notification_id: str,
    service: GigSuggestionService = Depends(get_gig_suggestion_service),
) -> dict:
    return service.dismiss_kid_notification(notification_id)
