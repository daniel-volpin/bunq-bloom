import base64

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
    return GigService(
        state_repository=StateRepository(tmp_path / "state.json"),
        photo_repository=PhotoRepository(tmp_path / "uploads"),
        verification_client=FakeVerificationClient(),
        payment_service=PaymentService(FakePaymentClient()),
    )


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

