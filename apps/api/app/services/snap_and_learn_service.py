from decimal import Decimal, ROUND_CEILING
from typing import Any

from app.errors import AppError


_AI_NOT_CONFIGURED_ERROR_CODES = {"analysis_not_configured", "report_generation_not_configured", "verification_not_configured"}


class SnapAndLearnService:
    def __init__(
        self,
        *,
        state_repository,
        photo_repository,
        analysis_client: Any,
        payment_service,
        allow_ai_fallback: bool = False,
    ):
        self.state_repository = state_repository
        self.photo_repository = photo_repository
        self.analysis_client = analysis_client
        self.payment_service = payment_service
        self.allow_ai_fallback = allow_ai_fallback

    def analyze(self, image_base64: str) -> dict:
        self.photo_repository.validate_data_url(image_base64)
        with self.state_repository.transaction() as state:
            kid_balance = self.payment_service.get_kid_balance(state)

        try:
            analysis = self.analysis_client.analyze(image_base64=image_base64)
        except AppError as exc:
            if not self.allow_ai_fallback or exc.code not in _AI_NOT_CONFIGURED_ERROR_CODES:
                raise
            analysis = self._fallback_analysis()
        except Exception as exc:
            if not self.allow_ai_fallback:
                raise AppError(
                    "analysis_failed",
                    "Snap & Learn analysis failed. Try again.",
                    status_code=502,
                    retryable=True,
                ) from exc
            analysis = self._fallback_analysis()

        state = self.state_repository.load()
        gigs_needed = self._gigs_needed(
            price_amount=analysis["estimated_price"]["amount"],
            balance_amount=kid_balance["amount"],
            state=state,
        )
        ai_mode = self._ai_response_mode(analysis)
        payment_mode = getattr(self.payment_service.payment_client, "mode", "fake_local")
        mode = self._response_mode(ai_mode, payment_mode)

        return {
            "analysis": {
                "item_name": analysis["item_name"],
                "estimated_price": analysis["estimated_price"],
                "gigs_needed": gigs_needed,
                "suggested_goal": self._suggested_goal(analysis["item_name"], gigs_needed),
                "confidence": analysis.get("confidence"),
            },
            "kid_balance": kid_balance,
            "mode": mode,
            "ai_mode": ai_mode,
            "payment_mode": payment_mode,
            "fallback_mode": analysis.get("raw_provider") == "fallback",
        }

    def _gigs_needed(self, *, price_amount: str, balance_amount: str, state: dict) -> int:
        remaining = max(Decimal(price_amount) - Decimal(balance_amount), Decimal("0.00"))
        if remaining == 0:
            return 0

        gig_rewards = [
            Decimal(gig["reward_amount"])
            for gig in state.get("gigs", {}).values()
            if gig.get("currency") == "EUR"
            and gig.get("status") in {"open", "claimed", "awaiting_after_photo"}
            and Decimal(gig["reward_amount"]) > 0
        ]
        baseline_reward = max(gig_rewards, default=Decimal("5.00"))
        return int((remaining / baseline_reward).to_integral_value(rounding=ROUND_CEILING))

    def _suggested_goal(self, item_name: str, gigs_needed: int) -> str:
        if gigs_needed <= 0:
            return f"You already have enough saved for {item_name}."
        if gigs_needed == 1:
            return f"Save for {item_name} by completing 1 more gig."
        return f"Save for {item_name} by completing {gigs_needed} more gigs."

    def _fallback_analysis(self) -> dict:
        return {
            "item_name": "Mystery item",
            "estimated_price": {"amount": "30.00", "currency": "EUR"},
            "confidence": 0,
            "reasoning_summary": "Fallback analysis used because AI was unavailable.",
            "raw_provider": "fallback",
            "raw_model": "snap-fallback-v1",
        }

    def _ai_response_mode(self, analysis: dict) -> str:
        if analysis.get("raw_provider") == "fallback":
            return "fallback"
        if analysis.get("raw_provider") == "fake":
            return "fake"
        return "real"

    def _response_mode(self, ai_mode: str, payment_mode: str) -> str:
        if ai_mode == "fallback":
            return "ai_fallback"
        if payment_mode == "fake_local":
            return "fake_local"
        return "real"
