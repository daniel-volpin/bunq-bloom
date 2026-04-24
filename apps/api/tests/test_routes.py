import base64

from fastapi.testclient import TestClient

from app.dependencies import get_gig_service
from app.integrations.fake_payment_client import FakePaymentClient
from app.integrations.fake_verification_client import FakeVerificationClient
from app.main import create_app
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


def make_client(tmp_path) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_gig_service] = lambda: make_service(tmp_path)
    return TestClient(app)


def test_health_route_reports_fake_integrations():
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_complete_route_runs_fake_core_loop(tmp_path):
    client = make_client(tmp_path)

    assert client.post("/api/gigs/gig_001/claim").status_code == 200
    before = client.post(
        "/api/gigs/gig_001/before-photo",
        json={"image_base64": image_data_url(b"before")},
    )
    assert before.status_code == 200

    complete = client.post(
        "/api/gigs/gig_001/complete",
        json={
            "after_image_base64": image_data_url(b"after"),
            "idempotency_key": "attempt-001",
        },
    )

    assert complete.status_code == 200
    body = complete.json()
    assert body["gig"]["status"] == "paid"
    assert body["verification"]["approved"] is True
    assert body["payment"]["status"] == "succeeded"
    assert body["kid_balance"]["amount"] == "27.50"

