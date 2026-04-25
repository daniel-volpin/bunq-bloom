from decimal import Decimal, InvalidOperation
from typing import Any

from app.errors import AppError
from app.models.domain import new_id, now_iso
from app.repositories.state_repository import StateRepository


class GigSuggestionService:
    def __init__(self, *, state_repository: StateRepository):
        self.state_repository = state_repository

    def list_suggestions(self) -> dict[str, list[dict[str, Any]]]:
        state = self.state_repository.load()
        suggestions = sorted(
            state.setdefault("gig_suggestions", {}).values(),
            key=lambda suggestion: suggestion["created_at"],
            reverse=True,
        )
        return {"suggestions": suggestions}

    def create_suggestion(self, payload) -> dict[str, dict[str, Any]]:
        title = payload.title.strip()
        reward_amount = self._normalize_reward(payload.reward_amount)
        checklist = [step.strip() for step in payload.verification_checklist if step.strip()]
        if not title:
            raise AppError("invalid_title", "Gig suggestion title is required.")
        if payload.currency != "EUR":
            raise AppError("invalid_currency", "Only EUR is supported for the MVP.")
        if not checklist:
            raise AppError("missing_checklist", "Add at least one checklist step.")

        now = now_iso()
        suggestion_id = new_id("suggestion")
        suggestion = {
            "id": suggestion_id,
            "family_id": "family_001",
            "suggested_by_user_id": "kid_001",
            "title": title,
            "description": payload.description.strip(),
            "reward_amount": reward_amount,
            "currency": payload.currency,
            "verification_checklist": checklist,
            "status": "pending",
            "approved_gig_id": None,
            "created_at": now,
            "updated_at": now,
        }

        with self.state_repository.transaction() as state:
            state.setdefault("gig_suggestions", {})[suggestion_id] = suggestion
            return {"suggestion": suggestion}

    def approve_suggestion(self, suggestion_id: str) -> dict[str, dict[str, Any]]:
        with self.state_repository.transaction() as state:
            suggestion = self._get_suggestion(state, suggestion_id)
            if suggestion["status"] != "pending":
                raise AppError(
                    "invalid_suggestion_state",
                    "Only pending gig suggestions can be approved.",
                    status_code=409,
                )

            now = now_iso()
            gig = self._gig_from_suggestion(suggestion, now)
            notification = self._approval_notification(suggestion=suggestion, gig_id=gig["id"], created_at=now)

            suggestion["status"] = "approved"
            suggestion["approved_gig_id"] = gig["id"]
            suggestion["updated_at"] = now
            state.setdefault("gigs", {})[gig["id"]] = gig
            state.setdefault("notifications", {})[notification["id"]] = notification

            return {"suggestion": suggestion, "gig": gig, "notification": notification}

    def list_kid_notifications(self) -> dict[str, list[dict[str, Any]]]:
        state = self.state_repository.load()
        notifications = [
            notification
            for notification in state.setdefault("notifications", {}).values()
            if notification["user_id"] == "kid_001" and not notification["read"]
        ]
        notifications.sort(key=lambda notification: notification["created_at"], reverse=True)
        return {"notifications": notifications}

    def dismiss_kid_notification(self, notification_id: str) -> dict[str, dict[str, Any]]:
        with self.state_repository.transaction() as state:
            notification = self._get_notification(state, notification_id)
            if notification["user_id"] != "kid_001":
                raise AppError("notification_not_found", "Notification was not found.", status_code=404)
            notification["read"] = True
            return {"notification": notification}

    def _get_suggestion(self, state: dict[str, Any], suggestion_id: str) -> dict[str, Any]:
        try:
            return state.setdefault("gig_suggestions", {})[suggestion_id]
        except KeyError as exc:
            raise AppError("suggestion_not_found", "Gig suggestion was not found.", status_code=404) from exc

    def _get_notification(self, state: dict[str, Any], notification_id: str) -> dict[str, Any]:
        try:
            return state.setdefault("notifications", {})[notification_id]
        except KeyError as exc:
            raise AppError("notification_not_found", "Notification was not found.", status_code=404) from exc

    def _normalize_reward(self, value: str) -> str:
        try:
            amount = Decimal(value)
        except (InvalidOperation, ValueError) as exc:
            raise AppError("invalid_reward_amount", "Reward amount must be a valid number.") from exc
        if amount <= 0:
            raise AppError("invalid_reward_amount", "Reward amount must be greater than zero.")
        return f"{amount:.2f}"

    def _gig_from_suggestion(self, suggestion: dict[str, Any], created_at: str) -> dict[str, Any]:
        return {
            "id": new_id("gig"),
            "family_id": suggestion["family_id"],
            "title": suggestion["title"],
            "description": suggestion["description"],
            "reward_amount": suggestion["reward_amount"],
            "currency": suggestion["currency"],
            "status": "open",
            "created_by_user_id": "parent_001",
            "claimed_by_user_id": None,
            "verification_checklist": suggestion["verification_checklist"],
            "before_photo_id": None,
            "after_photo_id": None,
            "verification_result_id": None,
            "payment_id": None,
            "created_at": created_at,
            "updated_at": created_at,
        }

    def _approval_notification(
        self,
        *,
        suggestion: dict[str, Any],
        gig_id: str,
        created_at: str,
    ) -> dict[str, Any]:
        return {
            "id": new_id("notification"),
            "user_id": suggestion["suggested_by_user_id"],
            "type": "gig_suggestion_approved",
            "title": "Gig approved",
            "message": f"Your gig idea was approved: {suggestion['title']}.",
            "gig_id": gig_id,
            "suggestion_id": suggestion["id"],
            "read": False,
            "created_at": created_at,
        }
