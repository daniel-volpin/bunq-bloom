import base64
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock
from time import sleep

import pytest

from app.errors import AppError
from app.integrations.fake_payment_client import FakePaymentClient
from app.integrations.fake_verification_client import FakeVerificationClient
from app.repositories.photo_repository import PhotoRepository
from app.repositories.state_repository import StateRepository
from app.services.gig_service import GigService
from app.services.payment_service import PaymentService


def image_data_url(payload: bytes = b"fake-image") -> str:
    encoded = base64.b64encode(payload).decode()
    return f"data:image/png;base64,{encoded}"


def make_service(tmp_path) -> GigService:
    return make_service_with_clients(tmp_path, FakeVerificationClient(), FakePaymentClient())


def make_service_with_clients(tmp_path, verification_client, payment_client) -> GigService:
    return GigService(
        state_repository=StateRepository(tmp_path / "state.json"),
        photo_repository=PhotoRepository(tmp_path / "uploads"),
        verification_client=verification_client,
        payment_service=PaymentService(payment_client),
    )


def make_service_with_ai_fallback(tmp_path, verification_client) -> GigService:
    return GigService(
        state_repository=StateRepository(tmp_path / "state.json"),
        photo_repository=PhotoRepository(tmp_path / "uploads"),
        verification_client=verification_client,
        payment_service=PaymentService(FakePaymentClient()),
        allow_ai_fallback=True,
    )


class CountingVerificationClient(FakeVerificationClient):
    def __init__(self):
        self.calls = 0

    def verify(self, **kwargs):
        self.calls += 1
        return super().verify(**kwargs)


class FailThenSucceedPaymentClient(FakePaymentClient):
    def __init__(self):
        self.calls = 0

    def create_parent_to_kid_payment(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            raise AppError("payment_failed", "Simulated payment failure.", retryable=True)
        return super().create_parent_to_kid_payment(**kwargs)


class SlowRealPaymentClient:
    mode = "real"
    parent_account_id = "parent_001"
    kid_account_id = "kid_001"

    def __init__(self):
        self.calls = 0
        self._lock = Lock()

    def create_parent_to_kid_payment(self, **kwargs):
        with self._lock:
            self.calls += 1
        sleep(0.05)
        return {
            "status": "succeeded",
            "amount": kwargs["amount"],
            "currency": kwargs["currency"],
            "bunq_payment_id": f"bunq_payment_{self.calls}",
        }

    def get_kid_balance(self, state=None):
        return {"amount": "27.50", "currency": "EUR", "source": "bunq"}


class RealPaymentBalanceFailureClient(SlowRealPaymentClient):
    def get_kid_balance(self, state=None):
        raise AppError("balance_refresh_failed", "Balance refresh failed.", status_code=502, retryable=True)


class UnknownStatePaymentClient(SlowRealPaymentClient):
    def create_parent_to_kid_payment(self, **kwargs):
        with self._lock:
            self.calls += 1
        raise AppError("payment_state_unknown", "Payment state is unknown.", status_code=502, retryable=False)


class BrokenVerificationClient:
    def verify(self, **kwargs):
        raise RuntimeError("vision unavailable")


class RealVerificationClient(FakeVerificationClient):
    def verify(self, **kwargs):
        result = super().verify(**kwargs)
        result["raw_provider"] = "lmstudio"
        result["raw_model"] = "qwen3.5-9b-mlx"
        return result


class FakeAiRealPaymentClient(FakePaymentClient):
    mode = "real"
    parent_account_id = "parent_001"
    kid_account_id = "kid_001"

    def get_kid_balance(self, state=None):
        return {"amount": "27.50", "currency": "EUR", "source": "bunq"}


def test_seeded_gig_can_complete_with_fake_adapters(tmp_path):
    service = make_service(tmp_path)

    service.claim_gig("gig_001")
    service.add_before_photo("gig_001", image_data_url(b"before"))
    result = service.complete_gig(
        "gig_001",
        after_image_base64=image_data_url(b"after"),
        idempotency_key="attempt-001",
    )

    assert result["gig"]["status"] == "paid"
    assert result["verification"]["approved"] is True
    assert result["payment"]["status"] == "succeeded"
    assert result["kid_balance"]["amount"] == "27.50"
    assert result["mode"] == "fake_local"
    assert result["fallback_mode"] is False


def test_completion_idempotency_does_not_double_pay(tmp_path):
    service = make_service(tmp_path)

    service.claim_gig("gig_001")
    service.add_before_photo("gig_001", image_data_url(b"before"))
    first = service.complete_gig(
        "gig_001",
        after_image_base64=image_data_url(b"after-one"),
        idempotency_key="attempt-001",
    )
    second = service.complete_gig(
        "gig_001",
        after_image_base64=image_data_url(b"after-two"),
        idempotency_key="attempt-001",
    )

    assert second == first
    assert service.get_kid_balance()["balance"]["amount"] == "27.50"


def test_paid_gig_with_new_idempotency_key_does_not_double_pay(tmp_path):
    service = make_service(tmp_path)

    service.claim_gig("gig_001")
    service.add_before_photo("gig_001", image_data_url(b"before"))
    first = service.complete_gig(
        "gig_001",
        after_image_base64=image_data_url(b"after-one"),
        idempotency_key="attempt-001",
    )
    second = service.complete_gig(
        "gig_001",
        after_image_base64=image_data_url(b"after-two"),
        idempotency_key="attempt-002",
    )

    assert first["payment"]["bunq_payment_id"] == second["payment"]["bunq_payment_id"]
    assert second["gig"]["status"] == "paid"
    assert service.get_kid_balance()["balance"]["amount"] == "27.50"


def test_payment_retry_does_not_rerun_verification(tmp_path):
    verification_client = CountingVerificationClient()
    payment_client = FailThenSucceedPaymentClient()
    service = make_service_with_clients(tmp_path, verification_client, payment_client)

    service.claim_gig("gig_001")
    service.add_before_photo("gig_001", image_data_url(b"before"))
    failed = service.complete_gig(
        "gig_001",
        after_image_base64=image_data_url(b"after-one"),
        idempotency_key="attempt-001",
    )
    retried = service.complete_gig(
        "gig_001",
        after_image_base64=image_data_url(b"after-two"),
        idempotency_key="attempt-002",
    )

    assert failed["gig"]["status"] == "payment_failed"
    assert failed["payment"]["status"] == "failed"
    assert failed["payment"]["retryable"] is True
    assert retried["gig"]["status"] == "paid"
    assert retried["payment"]["status"] == "succeeded"
    assert verification_client.calls == 1
    assert payment_client.calls == 2
    assert service.get_kid_balance()["balance"]["amount"] == "27.50"


def test_ai_fallback_can_approve_when_explicitly_enabled(tmp_path):
    service = make_service_with_ai_fallback(tmp_path, BrokenVerificationClient())

    service.claim_gig("gig_001")
    service.add_before_photo("gig_001", image_data_url(b"before"))
    result = service.complete_gig(
        "gig_001",
        after_image_base64=image_data_url(b"after"),
        idempotency_key="attempt-001",
    )

    assert result["gig"]["status"] == "paid"
    assert result["verification"]["approved"] is True
    assert result["verification"]["confidence"] == 0
    assert result["verification"]["message_for_kid"].startswith("Demo fallback approved")
    assert result["mode"] == "ai_fallback"
    assert result["fallback_mode"] is True


def test_real_ai_with_fake_payment_reports_fake_payment_mode(tmp_path):
    service = make_service_with_clients(tmp_path, RealVerificationClient(), FakePaymentClient())

    service.claim_gig("gig_001")
    service.add_before_photo("gig_001", image_data_url(b"before"))
    result = service.complete_gig(
        "gig_001",
        after_image_base64=image_data_url(b"after"),
        idempotency_key="attempt-001",
    )

    assert result["gig"]["status"] == "paid"
    assert result["payment"]["status"] == "succeeded"
    assert result["mode"] == "fake_local"
    assert result["ai_mode"] == "real"
    assert result["payment_mode"] == "fake_local"
    assert result["fallback_mode"] is False


def test_fake_ai_with_real_payment_reports_fake_ai_mode(tmp_path):
    service = make_service_with_clients(tmp_path, FakeVerificationClient(), FakeAiRealPaymentClient())

    service.claim_gig("gig_001")
    service.add_before_photo("gig_001", image_data_url(b"before"))
    result = service.complete_gig(
        "gig_001",
        after_image_base64=image_data_url(b"after"),
        idempotency_key="attempt-001",
    )

    assert result["gig"]["status"] == "paid"
    assert result["mode"] == "fake_ai"
    assert result["ai_mode"] == "fake"
    assert result["payment_mode"] == "real"
    assert result["fallback_mode"] is False


def test_concurrent_completion_only_creates_one_real_payment(tmp_path):
    payment_client = SlowRealPaymentClient()
    service = make_service_with_clients(tmp_path, RealVerificationClient(), payment_client)

    service.claim_gig("gig_001")
    service.add_before_photo("gig_001", image_data_url(b"before"))
    barrier = Barrier(2)

    def complete(idempotency_key: str) -> dict:
        barrier.wait(timeout=2)
        return service.complete_gig(
            "gig_001",
            after_image_base64=image_data_url(idempotency_key.encode()),
            idempotency_key=idempotency_key,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(complete, ["attempt-001", "attempt-002"]))

    assert payment_client.calls == 1
    assert {result["gig"]["status"] for result in results} == {"paid"}
    assert {result["payment"]["bunq_payment_id"] for result in results} == {"bunq_payment_1"}


def test_successful_payment_is_not_marked_failed_when_balance_refresh_fails(tmp_path):
    payment_client = RealPaymentBalanceFailureClient()
    service = make_service_with_clients(tmp_path, RealVerificationClient(), payment_client)

    service.claim_gig("gig_001")
    service.add_before_photo("gig_001", image_data_url(b"before"))
    result = service.complete_gig(
        "gig_001",
        after_image_base64=image_data_url(b"after"),
        idempotency_key="attempt-001",
    )
    retried = service.complete_gig(
        "gig_001",
        after_image_base64=image_data_url(b"after-again"),
        idempotency_key="attempt-002",
    )

    assert result["gig"]["status"] == "paid"
    assert result["payment"]["status"] == "succeeded"
    assert result["balance_refresh_status"] == "failed"
    assert result["balance_refresh_error"] == "balance_refresh_failed"
    assert retried["payment"]["bunq_payment_id"] == result["payment"]["bunq_payment_id"]
    assert payment_client.calls == 1


def test_unknown_payment_state_blocks_retry_to_avoid_duplicate_payment(tmp_path):
    payment_client = UnknownStatePaymentClient()
    service = make_service_with_clients(tmp_path, RealVerificationClient(), payment_client)

    service.claim_gig("gig_001")
    service.add_before_photo("gig_001", image_data_url(b"before"))
    result = service.complete_gig(
        "gig_001",
        after_image_base64=image_data_url(b"after"),
        idempotency_key="attempt-001",
    )

    assert result["gig"]["status"] == "payment_failed"
    assert result["payment"]["retryable"] is False
    with pytest.raises(AppError) as exc_info:
        service.retry_payment("gig_001", idempotency_key="retry-001")

    assert exc_info.value.code == "payment_not_retryable"
    assert payment_client.calls == 1


def test_ai_failure_without_fallback_is_retryable_error(tmp_path):
    service = make_service_with_clients(tmp_path, BrokenVerificationClient(), FakePaymentClient())

    service.claim_gig("gig_001")
    service.add_before_photo("gig_001", image_data_url(b"before"))

    with pytest.raises(AppError, match="verification_failed") as exc_info:
        service.complete_gig(
            "gig_001",
            after_image_base64=image_data_url(b"after"),
            idempotency_key="attempt-001",
        )

    assert exc_info.value.code == "verification_failed"
    assert exc_info.value.status_code == 502
    assert exc_info.value.retryable is True


class UnconfiguredVerificationClient:
    def verify(self, **kwargs):
        raise AppError("verification_not_configured", "AI provider is not configured.", status_code=500)


def test_unconfigured_ai_is_reported_without_masking_as_retryable_failure(tmp_path):
    service = make_service_with_clients(tmp_path, UnconfiguredVerificationClient(), FakePaymentClient())

    service.claim_gig("gig_001")
    service.add_before_photo("gig_001", image_data_url(b"before"))

    with pytest.raises(AppError, match="verification_not_configured") as exc_info:
        service.complete_gig(
            "gig_001",
            after_image_base64=image_data_url(b"after"),
            idempotency_key="attempt-001",
        )

    assert exc_info.value.code == "verification_not_configured"
    assert exc_info.value.status_code == 500
    assert exc_info.value.retryable is False


def test_unconfigured_ai_can_fallback_when_explicitly_enabled(tmp_path):
    service = make_service_with_ai_fallback(tmp_path, UnconfiguredVerificationClient())

    service.claim_gig("gig_001")
    service.add_before_photo("gig_001", image_data_url(b"before"))

    result = service.complete_gig(
        "gig_001",
        after_image_base64=image_data_url(b"after"),
        idempotency_key="attempt-001",
    )

    assert result["gig"]["status"] == "paid"
    assert result["verification"]["approved"] is True
    assert result["mode"] == "ai_fallback"
    assert result["fallback_mode"] is True


def test_retry_payment_requires_payment_failed_status(tmp_path):
    verification_client = CountingVerificationClient()
    payment_client = FakePaymentClient()
    service = make_service_with_clients(tmp_path, verification_client, payment_client)

    service.claim_gig("gig_001")
    service.add_before_photo("gig_001", image_data_url(b"before"))

    with pytest.raises(AppError) as exc_info:
        service.retry_payment("gig_001", idempotency_key="retry-001")

    assert exc_info.value.code == "invalid_gig_state"
    assert payment_client.mode == "fake_local"
    assert verification_client.calls == 0


def test_retry_payment_reuses_approved_verification_without_new_after_photo(tmp_path):
    verification_client = CountingVerificationClient()
    payment_client = FailThenSucceedPaymentClient()
    service = make_service_with_clients(tmp_path, verification_client, payment_client)

    service.claim_gig("gig_001")
    service.add_before_photo("gig_001", image_data_url(b"before"))
    failed = service.complete_gig(
        "gig_001",
        after_image_base64=image_data_url(b"after-one"),
        idempotency_key="attempt-001",
    )

    retried = service.retry_payment("gig_001", idempotency_key="retry-001")

    assert failed["gig"]["status"] == "payment_failed"
    assert retried["gig"]["status"] == "paid"
    assert retried["payment"]["status"] == "succeeded"
    assert retried["payment"]["bunq_payment_id"] is not None
    assert retried["kid_balance"]["amount"] == "27.50"
    assert verification_client.calls == 1
    assert payment_client.calls == 2


def test_before_photo_rejects_unsupported_image_type(tmp_path):
    service = make_service(tmp_path)

    service.claim_gig("gig_001")

    with pytest.raises(AppError) as exc_info:
        service.add_before_photo(
            "gig_001",
            "data:image/gif;base64,R0lGODlhAQABAIAAAAUEBA==",
        )

    assert exc_info.value.code == "invalid_image_type"
    assert exc_info.value.status_code == 400


def test_before_photo_rejects_oversized_payload(tmp_path):
    service = make_service(tmp_path)

    service.claim_gig("gig_001")

    with pytest.raises(AppError) as exc_info:
        service.add_before_photo("gig_001", image_data_url(b"a" * (8 * 1024 * 1024 + 1)))

    assert exc_info.value.code == "image_too_large"
    assert exc_info.value.status_code == 413


def test_complete_gig_rejects_oversized_after_photo(tmp_path):
    service = make_service(tmp_path)

    service.claim_gig("gig_001")
    service.add_before_photo("gig_001", image_data_url(b"before"))

    with pytest.raises(AppError) as exc_info:
        service.complete_gig(
            "gig_001",
            after_image_base64=image_data_url(b"a" * (8 * 1024 * 1024 + 1)),
            idempotency_key="attempt-001",
        )

    assert exc_info.value.code == "image_too_large"
    assert exc_info.value.status_code == 413
