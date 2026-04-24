import base64

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


class BrokenVerificationClient:
    def verify(self, **kwargs):
        raise RuntimeError("vision unavailable")


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


def test_ai_failure_without_fallback_is_retryable_error(tmp_path):
    service = make_service_with_clients(tmp_path, BrokenVerificationClient(), FakePaymentClient())

    service.claim_gig("gig_001")
    service.add_before_photo("gig_001", image_data_url(b"before"))

    try:
        service.complete_gig(
            "gig_001",
            after_image_base64=image_data_url(b"after"),
            idempotency_key="attempt-001",
        )
    except AppError as exc:
        assert exc.code == "verification_failed"
        assert exc.status_code == 502
        assert exc.retryable is True
    else:
        raise AssertionError("Expected verification failure")
