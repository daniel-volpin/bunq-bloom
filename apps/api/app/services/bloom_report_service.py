import hashlib
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import logging
from copy import deepcopy
from typing import Any, Callable

from app.errors import AppError


_AI_NOT_CONFIGURED_ERROR_CODES = {"analysis_not_configured", "report_generation_not_configured", "verification_not_configured"}
logger = logging.getLogger(__name__)


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

        weekly_payments = self._weekly_payments(
            payments=state.get("payments", {}).values(),
            start_date=start_date,
            end_date=end_date,
        )

        cache_fingerprint = self._cache_fingerprint(
            current_date=end_date.isoformat(),
            current_balance=current_balance,
            weekly_payments=weekly_payments,
        )
        cached_report = self._cached_report(
            state=state,
            current_date=end_date.isoformat(),
            fingerprint=cache_fingerprint,
        )
        if cached_report is not None:
            return cached_report

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
                logger.warning("Weekly Bloom Report AI generation returned AppError: %s", exc.code)
                if not self.allow_ai_fallback or exc.code not in _AI_NOT_CONFIGURED_ERROR_CODES:
                    raise
                mode = "ai_fallback"
                fallback_mode = True
            except Exception as exc:
                logger.exception("Weekly Bloom Report AI generation failed")
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
        self._store_cached_report(
            current_date=end_date.isoformat(),
            fingerprint=cache_fingerprint,
            generated_at=now.isoformat(),
            report=report,
        )
        return report

    def _weekly_payments(self, *, payments, start_date, end_date) -> list[dict]:
        weekly_payments = []
        for payment in payments:
            if payment.get("status") != "succeeded":
                continue
            payment_date = self._parse_iso_date(payment.get("created_at"))
            if payment_date is None or payment_date < start_date or payment_date > end_date:
                continue
            weekly_payments.append(payment)
        return weekly_payments

    def _cache_fingerprint(
        self,
        *,
        current_date: str,
        current_balance: dict,
        weekly_payments: list[dict],
    ) -> str:
        payment_snapshot = sorted(
            [
                {
                    "id": payment.get("id"),
                    "gig_id": payment.get("gig_id"),
                    "amount": payment.get("amount"),
                    "currency": payment.get("currency"),
                    "status": payment.get("status"),
                    "created_at": payment.get("created_at"),
                    "updated_at": payment.get("updated_at"),
                }
                for payment in weekly_payments
            ],
            key=lambda payment: str(payment.get("id") or ""),
        )
        payload = {
            "current_date": current_date,
            "current_balance": current_balance,
            "weekly_payments": payment_snapshot,
            "narrative_mode": getattr(self.narrative_client, "mode", "none") if self.narrative_client else "none",
            "narrative_model": getattr(self.narrative_client, "model", None) if self.narrative_client else None,
            "allow_ai_fallback": self.allow_ai_fallback,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _cached_report(self, *, state: dict, current_date: str, fingerprint: str) -> dict | None:
        entry = state.get("report_cache", {}).get("weekly")
        if not isinstance(entry, dict):
            return None
        if entry.get("current_date") != current_date:
            return None
        if entry.get("fingerprint") != fingerprint:
            return None
        report = entry.get("report")
        if not isinstance(report, dict):
            return None
        return deepcopy(report)

    def _store_cached_report(
        self,
        *,
        current_date: str,
        fingerprint: str,
        generated_at: str,
        report: dict,
    ) -> None:
        with self.state_repository.transaction() as state:
            report_cache = state.setdefault("report_cache", {})
            report_cache["weekly"] = {
                "current_date": current_date,
                "fingerprint": fingerprint,
                "generated_at": generated_at,
                "report": deepcopy(report),
            }

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