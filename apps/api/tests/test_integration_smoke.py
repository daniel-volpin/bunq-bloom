import base64
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.integrations.bunq_payment_client import BunqPaymentClient
from app.integrations.lmstudio_client import LMStudioVisionClient


_SMOKE_FLAG = "BLOOM_RUN_SMOKE_TESTS"
_PAYMENT_SMOKE_FLAG = "BLOOM_RUN_BUNQ_PAYMENT_SMOKE"


def _require_enabled() -> None:
    if os.getenv(_SMOKE_FLAG, "").lower() not in {"1", "true", "yes"}:
        pytest.skip(f"Set {_SMOKE_FLAG}=true to run real-provider smoke tests.")


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        pytest.skip(f"Set {name} to run this smoke test.")
    return value


def _tiny_png_data_url() -> str:
    payload = base64.b64encode(
        bytes.fromhex(
            "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C489"
            "0000000D49444154789C6360606060000000040001F61738550000000049454E44AE426082"
        )
    ).decode("ascii")
    return f"data:image/png;base64,{payload}"


def test_lmstudio_snap_and_learn_smoke() -> None:
    _require_enabled()
    base_url = _require_env("BLOOM_LMSTUDIO_BASE_URL")
    model = _require_env("BLOOM_LMSTUDIO_MODEL")
    api_key = os.getenv("BLOOM_LMSTUDIO_API_KEY")

    client = LMStudioVisionClient(
        base_url=base_url,
        model=model,
        api_key=api_key,
    )

    result = client.analyze(image_base64=_tiny_png_data_url())

    assert result["raw_provider"] == "lmstudio"
    assert result["raw_model"]
    assert result["item_name"]
    assert result["estimated_price"]["currency"] == "EUR"


def test_bunq_balance_smoke() -> None:
    _require_enabled()
    api_key = _require_env("BUNQ_API_KEY")
    parent_account_id = _require_env("BUNQ_PARENT_ACCOUNT_ID")
    kid_account_id = _require_env("BUNQ_KID_ACCOUNT_ID")
    toolkit_path = _require_env("BLOOM_BUNQ_TOOLKIT_PATH")

    settings = SimpleNamespace(
        bunq_api_key=api_key,
        bunq_parent_account_id=parent_account_id,
        bunq_kid_account_id=kid_account_id,
        bunq_toolkit_path=Path(toolkit_path),
        resolved_bunq_toolkit_path=lambda: Path(toolkit_path).resolve(),
    )
    client = BunqPaymentClient(settings)

    balance = client.get_kid_balance()

    assert balance["currency"] == "EUR"
    assert balance["source"] == "bunq"
    assert balance["amount"]


def test_bunq_tiny_payment_smoke() -> None:
    _require_enabled()
    if os.getenv(_PAYMENT_SMOKE_FLAG, "").lower() not in {"1", "true", "yes"}:
        pytest.skip(f"Set {_PAYMENT_SMOKE_FLAG}=true to create a real sandbox payment.")

    api_key = _require_env("BUNQ_API_KEY")
    parent_account_id = _require_env("BUNQ_PARENT_ACCOUNT_ID")
    kid_account_id = _require_env("BUNQ_KID_ACCOUNT_ID")
    toolkit_path = _require_env("BLOOM_BUNQ_TOOLKIT_PATH")
    amount = os.getenv("BLOOM_BUNQ_SMOKE_PAYMENT_AMOUNT", "0.01")

    settings = SimpleNamespace(
        bunq_api_key=api_key,
        bunq_parent_account_id=parent_account_id,
        bunq_kid_account_id=kid_account_id,
        bunq_toolkit_path=Path(toolkit_path),
        resolved_bunq_toolkit_path=lambda: Path(toolkit_path).resolve(),
    )
    client = BunqPaymentClient(settings)

    result = client.create_parent_to_kid_payment(
        amount=amount,
        currency="EUR",
        description="bunq Bloom smoke payment",
        idempotency_key="smoke-test-manual",
    )
    balance = client.get_kid_balance()

    assert result["status"] == "succeeded"
    assert result["bunq_payment_id"]
    assert balance["currency"] == "EUR"
    assert balance["source"] == "bunq"
