from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def money_add(value: str, delta: str) -> str:
    return f"{Decimal(value) + Decimal(delta):.2f}"


def seed_state() -> dict[str, Any]:
    now = now_iso()
    return {
        "families": {
            "family_001": {
                "id": "family_001",
                "name": "Bloom Demo Family",
                "parent_user_id": "parent_001",
                "kid_user_id": "kid_001",
                "parent_monetary_account_id": "fake_parent_account",
                "kid_monetary_account_id": "fake_kid_account",
            }
        },
        "users": {
            "parent_001": {"id": "parent_001", "role": "parent", "display_name": "Parent"},
            "kid_001": {"id": "kid_001", "role": "kid", "display_name": "Mila"},
        },
        "gigs": {
            "gig_001": {
                "id": "gig_001",
                "family_id": "family_001",
                "title": "Clean your room",
                "description": "Make the bed, clear the floor, and tidy the desk.",
                "reward_amount": "5.00",
                "currency": "EUR",
                "status": "open",
                "created_by_user_id": "parent_001",
                "claimed_by_user_id": None,
                "verification_checklist": ["bed made", "floor clear", "desk tidy"],
                "before_photo_id": None,
                "after_photo_id": None,
                "verification_result_id": None,
                "payment_id": None,
                "created_at": now,
                "updated_at": now,
            }
        },
        "photos": {},
        "verification_results": {},
        "payments": {},
        "completion_attempts": {},
        "gig_suggestions": {},
        "notifications": {},
        "report_cache": {},
        "balances": {
            "kid_001": {"amount": "22.50", "currency": "EUR", "source": "fake"},
        },
    }
