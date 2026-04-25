from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Callable

from app.errors import AppError


_AI_NOT_CONFIGURED_ERROR_CODES = {"analysis_not_configured", "report_generation_not_configured", "verification_not_configured"}


class BloomReportService:
    def __init__(
        self,
        *,
        state_repository,
        narrative_client: Any | None = None,
        allow_ai_fallback: bool = False,
        now_fn: Callable[[], datetime] | None = None,
    ):
        self.state_repository = state_repository
        self.narrative_client = narrative_client
        self.allow_ai_fallback = allow_ai_fallback
        self.now_fn = now_fn or (lambda: datetime.now(timezone.utc))

    def get_weekly_report(self) -> dict:
        state = self.state_repository.load()
        now = self.now_fn()
        start_date = now.date() - timedelta(days=6)
        end_date = now.date()

        current_balance = state["balances"].get(
            "kid_001",
            {"amount": "0.00", "currency": "EUR", "source": "unknown"},
        )

        weekly_payments = []
        for payment in state.get("payments", {}).values():
            if payment.get("status") != "succeeded":
                continue
            payment_date = self._parse_iso_date(payment.get("created_at"))
            if payment_date is None or payment_date < start_date or payment_date > end_date:
                continue
            weekly_payments.append(payment)

        total_earned = sum(Decimal(payment["amount"]) for payment in weekly_payments)
        gigs_completed = len(weekly_payments)
        average_reward = Decimal("0.00") if gigs_completed == 0 else total_earned / gigs_completed

        top_payment = max(weekly_payments, key=lambda payment: Decimal(payment["amount"]), default=None)
        top_gig_title = None
        if top_payment is not None:
            gig = state.get("gigs", {}).get(top_payment["gig_id"])
            top_gig_title = gig.get("title") if gig else "Unknown gig"

        report = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "stats": {
                "gigs_completed": gigs_completed,
                "money_earned": self._money(total_earned),
                "average_reward": self._money(average_reward),
                "current_balance": current_balance,
            },
            "highlights": self._highlights(
                gigs_completed=gigs_completed,
                total_earned=total_earned,
                top_gig_title=top_gig_title,
                top_payment=top_payment,
            ),
            "savings_insight": self._savings_insight(total_earned),
            "conversation_starter": self._conversation_starter(gigs_completed),
        }

        mode = "fake_local"
        fallback_mode = False
        if self.narrative_client is not None:
            try:
                narrative = self.narrative_client.generate_weekly_report(report_context=report)
                report["highlights"] = narrative["highlights"]
                report["savings_insight"] = narrative["savings_insight"]
                report["conversation_starter"] = narrative["conversation_starter"]
                mode = self._response_mode(narrative)
                fallback_mode = narrative.get("raw_provider") == "fallback"
            except AppError as exc:
                if not self.allow_ai_fallback or exc.code not in _AI_NOT_CONFIGURED_ERROR_CODES:
                    raise
                mode = "ai_fallback"
                fallback_mode = True
            except Exception as exc:
                if not self.allow_ai_fallback:
                    raise AppError(
                        "report_generation_failed",
                        "Weekly Bloom Report generation failed. Try again.",
                        status_code=502,
                        retryable=True,
                    ) from exc
                mode = "ai_fallback"
                fallback_mode = True

        report["mode"] = mode
        report["fallback_mode"] = fallback_mode
        return report

    def _highlights(
        self,
        *,
        gigs_completed: int,
        total_earned: Decimal,
        top_gig_title: str | None,
        top_payment: dict | None,
    ) -> list[dict]:
        if gigs_completed == 0:
            return [
                {
                    "title": "Weekly reset",
                    "detail": "No paid gigs were recorded this week yet.",
                }
            ]

        highlights = []
        if top_payment is not None and top_gig_title is not None:
            highlights.append(
                {
                    "title": "Top earning gig",
                    "detail": f"{top_gig_title} earned EUR {Decimal(top_payment['amount']):.2f} this week.",
                }
            )

        highlights.append(
            {
                "title": "Weekly momentum",
                "detail": f"{gigs_completed} paid gigs brought in EUR {total_earned:.2f} this week.",
            }
        )
        return highlights

    def _savings_insight(self, total_earned: Decimal) -> str:
        if total_earned == 0:
            return "No paid gigs landed this week yet. One completed gig can start the savings habit again."

        half_saved = total_earned / 2
        return f"You earned EUR {total_earned:.2f} this week. Saving half would set aside EUR {half_saved:.2f} for the next goal."

    def _conversation_starter(self, gigs_completed: int) -> str:
        if gigs_completed == 0:
            return "What is one small gig you want to finish first next week?"
        return "Which goal feels worth saving for with next week's gigs?"

    def _money(self, value: Decimal) -> dict:
        return {"amount": f"{value:.2f}", "currency": "EUR"}

    def _parse_iso_date(self, value: str | None):
        if not value:
            return None
        return datetime.fromisoformat(value).date()

    def _response_mode(self, narrative: dict) -> str:
        if narrative.get("raw_provider") == "fallback":
            return "ai_fallback"
        if narrative.get("raw_provider") == "fake":
            return "fake_local"
        return "real"