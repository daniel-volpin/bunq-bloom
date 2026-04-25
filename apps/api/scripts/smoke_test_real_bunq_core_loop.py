#!/usr/bin/env python3
"""
Run the bunq Bloom core loop against real bunq sandbox payment.

This intentionally uses deterministic fake AI verification so the smoke test
isolates the money path:
  parent posts gig -> kid claims -> before/after photos -> AI approves
  -> real bunq sandbox payment -> kid balance returned

Usage:
  cd apps/api
  python scripts/smoke_test_real_bunq_core_loop.py
  python scripts/smoke_test_real_bunq_core_loop.py --amount 0.05
"""

from __future__ import annotations

import argparse
import base64
import sys
import tempfile
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import SimpleNamespace

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.errors import AppError
from app.integrations.bunq_payment_client import BunqPaymentClient
from app.integrations.fake_verification_client import FakeVerificationClient
from app.repositories.photo_repository import PhotoRepository
from app.repositories.state_repository import StateRepository
from app.services.gig_service import GigService
from app.services.payment_service import PaymentService
from app.settings import Settings


def image_data_url(payload: bytes) -> str:
    encoded = base64.b64encode(payload).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def amount(value: str) -> str:
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError("Amount must be a decimal string, e.g. 0.01") from exc
    if parsed <= Decimal("0") or parsed > Decimal("5.00"):
        raise argparse.ArgumentTypeError("Amount must be greater than 0 and no more than 5.00")
    return f"{parsed:.2f}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke test the full core loop with real bunq sandbox payment.")
    parser.add_argument("--amount", type=amount, default="0.01", help="Sandbox gig reward amount. Default: 0.01")
    return parser.parse_args()


def main() -> int:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    args = parse_args()
    settings = Settings()

    missing = settings.bunq_missing_config_codes()
    if settings.use_fake_bunq or missing:
        print("Real bunq sandbox config is not ready.", file=sys.stderr)
        print("Set BLOOM_USE_FAKE_BUNQ=false and configure BUNQ_API_KEY, BUNQ_PARENT_ACCOUNT_ID, BUNQ_KID_ACCOUNT_ID.", file=sys.stderr)
        if missing:
            print(f"Missing config: {', '.join(missing)}", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="bloom_real_bunq_core_") as tmp:
        tmp_path = Path(tmp)
        service = GigService(
            state_repository=StateRepository(tmp_path / "state.json"),
            photo_repository=PhotoRepository(tmp_path / "uploads"),
            verification_client=FakeVerificationClient(),
            payment_service=PaymentService(BunqPaymentClient(settings)),
        )

        created = service.create_gig(
            SimpleNamespace(
                title="Real bunq smoke gig",
                description="Small sandbox transfer to verify the Bloom core loop.",
                reward_amount=args.amount,
                currency="EUR",
                verification_checklist=["before photo", "after photo"],
            )
        )
        gig_id = created["gig"]["id"]
        service.claim_gig(gig_id)
        service.add_before_photo(gig_id, image_data_url(b"before-smoke-photo"))
        try:
            result = service.complete_gig(
                gig_id,
                after_image_base64=image_data_url(b"after-smoke-photo"),
                idempotency_key="real-bunq-core-smoke-001",
            )
        except AppError as exc:
            print("Core loop smoke failed.", file=sys.stderr)
            print(f"code={exc.code} retryable={exc.retryable} message={exc.message}", file=sys.stderr)
            return 1

    payment = result["payment"] or {}
    balance = result["kid_balance"] or {}
    print("Core loop smoke result")
    print("-" * 80)
    print(f"gig_status={result['gig']['status']}")
    print(f"verification_approved={result['verification']['approved']}")
    print(f"payment_status={payment.get('status')}")
    print(f"payment_retryable={payment.get('retryable')}")
    print(f"payment_error_code={payment.get('error_code')}")
    print(f"payment_amount={payment.get('amount')} {payment.get('currency')}")
    print(f"bunq_payment_id={payment.get('bunq_payment_id')}")
    print(f"kid_balance={balance.get('amount')} {balance.get('currency')} source={balance.get('source')}")
    print(f"mode={result.get('mode')} ai_mode={result.get('ai_mode')} payment_mode={result.get('payment_mode')}")
    print(f"balance_refresh_status={result.get('balance_refresh_status', 'ok')}")

    return 0 if result["gig"]["status"] == "paid" and payment.get("status") == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
