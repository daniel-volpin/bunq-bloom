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
from app.services.bloom_report_service import BloomReportService
from app.services.snap_and_learn_service import SnapAndLearnService


class FailThenSucceedPaymentClient(FakePaymentClient):
    def __init__(self):
        self.calls = 0

    def create_parent_to_kid_payment(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            from app.errors import AppError

            raise AppError("payment_failed", "Simulated payment failure.", retryable=True)
        return super().create_parent_to_kid_payment(**kwargs)


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


def make_client_with_clients(tmp_path, verification_client, payment_client) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_gig_service] = lambda: GigService(
        state_repository=StateRepository(tmp_path / "state.json"),
        photo_repository=PhotoRepository(tmp_path / "uploads"),
        verification_client=verification_client,
        payment_service=PaymentService(payment_client),
    )
    return TestClient(app)


class FakeSnapAndLearnClient:
    mode = "fake"

    def analyze(self, *, image_base64: str) -> dict:
        return {
            "item_name": "Nintendo Switch Game",
            "estimated_price": {"amount": "24.99", "currency": "EUR"},
            "confidence": 0.91,
            "reasoning_summary": "Fake analysis recognized a game case.",
            "raw_provider": "fake",
            "raw_model": "fake-snap-v1",
        }


def make_snap_client(tmp_path) -> TestClient:
    from app.dependencies import get_snap_and_learn_service

    app = create_app()
    app.dependency_overrides[get_snap_and_learn_service] = lambda: SnapAndLearnService(
        state_repository=StateRepository(tmp_path / "state.json"),
        photo_repository=PhotoRepository(tmp_path / "uploads"),
        analysis_client=FakeSnapAndLearnClient(),
        payment_service=PaymentService(FakePaymentClient()),
    )
    return TestClient(app)


class FakeBloomNarrativeClient:
    mode = "fake"

    def generate_weekly_report(self, *, report_context: dict) -> dict:
        return {
            "highlights": [
                {"title": "Family win", "detail": "Two gigs turned effort into EUR 12.50 this week."}
            ],
            "savings_insight": "EUR 12.50 earned means EUR 6.25 could go straight into savings this week.",
            "conversation_starter": "Which reward felt most worth the effort this week?",
            "raw_provider": "fake",
            "raw_model": "fake-bloom-v1",
        }


def seed_bloom_report_state(tmp_path) -> None:
    repository = StateRepository(tmp_path / "state.json")
    state = repository.load()
    state["balances"]["kid_001"] = {"amount": "35.00", "currency": "EUR", "source": "fake"}
    state["gigs"]["gig_001"].update(
        {
            "status": "paid",
            "reward_amount": "5.00",
            "title": "Clean your room",
            "payment_id": "payment_001",
            "updated_at": "2026-04-22T10:00:00+00:00",
        }
    )
    state["payments"]["payment_001"] = {
        "id": "payment_001",
        "gig_id": "gig_001",
        "amount": "5.00",
        "currency": "EUR",
        "from_monetary_account_id": "fake_parent_account",
        "to_monetary_account_id": "fake_kid_account",
        "bunq_payment_id": "fake_payment_001",
        "status": "succeeded",
        "created_at": "2026-04-22T10:00:00+00:00",
        "updated_at": "2026-04-22T10:00:00+00:00",
    }
    state["gigs"]["gig_002"] = {
        "id": "gig_002",
        "family_id": "family_001",
        "title": "Walk the dog",
        "description": "Take the dog around the block.",
        "reward_amount": "7.50",
        "currency": "EUR",
        "status": "paid",
        "created_by_user_id": "parent_001",
        "claimed_by_user_id": "kid_001",
        "verification_checklist": ["dog walked"],
        "before_photo_id": None,
        "after_photo_id": None,
        "verification_result_id": None,
        "payment_id": "payment_002",
        "created_at": "2026-04-24T08:00:00+00:00",
        "updated_at": "2026-04-24T09:00:00+00:00",
    }
    state["payments"]["payment_002"] = {
        "id": "payment_002",
        "gig_id": "gig_002",
        "amount": "7.50",
        "currency": "EUR",
        "from_monetary_account_id": "fake_parent_account",
        "to_monetary_account_id": "fake_kid_account",
        "bunq_payment_id": "fake_payment_002",
        "status": "succeeded",
        "created_at": "2026-04-24T09:00:00+00:00",
        "updated_at": "2026-04-24T09:00:00+00:00",
    }
    repository.save(state)


def fixed_report_now():
    from datetime import datetime, timezone

    return datetime(2026, 4, 25, 12, 0, tzinfo=timezone.utc)


def make_bloom_report_client(tmp_path) -> TestClient:
    from app.dependencies import get_bloom_report_service

    seed_bloom_report_state(tmp_path)
    app = create_app()
    app.dependency_overrides[get_bloom_report_service] = lambda: BloomReportService(
        state_repository=StateRepository(tmp_path / "state.json"),
        narrative_client=FakeBloomNarrativeClient(),
        now_fn=fixed_report_now,
    )
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
    assert body["ai_mode"] == "fake"
    assert body["payment_mode"] == "fake_local"


def test_before_photo_route_rejects_unsupported_image_type(tmp_path):
    client = make_client(tmp_path)

    assert client.post("/api/gigs/gig_001/claim").status_code == 200

    response = client.post(
        "/api/gigs/gig_001/before-photo",
        json={"image_base64": "data:image/gif;base64,R0lGODlhAQABAIAAAAUEBA=="},
    )

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "invalid_image_type",
            "message": "Supported image types are JPEG, PNG, and WebP.",
            "retryable": False,
        }
    }


def test_complete_route_rejects_oversized_after_photo(tmp_path):
    client = make_client(tmp_path)

    assert client.post("/api/gigs/gig_001/claim").status_code == 200
    assert (
        client.post(
            "/api/gigs/gig_001/before-photo",
            json={"image_base64": image_data_url(b"before")},
        ).status_code
        == 200
    )

    response = client.post(
        "/api/gigs/gig_001/complete",
        json={
            "after_image_base64": image_data_url(b"a" * (8 * 1024 * 1024 + 1)),
            "idempotency_key": "attempt-001",
        },
    )

    assert response.status_code == 413
    assert response.json() == {
        "error": {
            "code": "image_too_large",
            "message": "Image must be 8 MB or smaller.",
            "retryable": False,
        }
    }


def test_retry_payment_route_recovers_payment_failed_gig(tmp_path):
    payment_client = FailThenSucceedPaymentClient()
    client = make_client_with_clients(tmp_path, FakeVerificationClient(), payment_client)

    assert client.post("/api/gigs/gig_001/claim").status_code == 200
    assert (
        client.post(
            "/api/gigs/gig_001/before-photo",
            json={"image_base64": image_data_url(b"before")},
        ).status_code
        == 200
    )

    failed = client.post(
        "/api/gigs/gig_001/complete",
        json={
            "after_image_base64": image_data_url(b"after"),
            "idempotency_key": "attempt-001",
        },
    )
    assert failed.status_code == 200
    assert failed.json()["gig"]["status"] == "payment_failed"

    retried = client.post(
        "/api/gigs/gig_001/retry-payment",
        json={"idempotency_key": "retry-001"},
    )

    assert retried.status_code == 200
    body = retried.json()
    assert body["gig"]["status"] == "paid"
    assert body["payment"]["status"] == "succeeded"
    assert body["kid_balance"]["amount"] == "27.50"
    assert payment_client.calls == 2


def test_snap_and_learn_route_returns_analysis_shape(tmp_path):
    client = make_snap_client(tmp_path)

    response = client.post(
        "/api/snap-and-learn/analyze",
        json={"image_base64": image_data_url(b"item-photo")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["analysis"]["item_name"] == "Nintendo Switch Game"
    assert body["analysis"]["estimated_price"] == {"amount": "24.99", "currency": "EUR"}
    assert body["analysis"]["gigs_needed"] == 1
    assert body["kid_balance"]["amount"] == "22.50"
    assert body["mode"] == "fake_local"
    assert body["ai_mode"] == "fake"
    assert body["payment_mode"] == "fake_local"
    assert body["fallback_mode"] is False


def test_bloom_report_route_returns_weekly_report_shape(tmp_path):
    client = make_bloom_report_client(tmp_path)

    response = client.get("/api/bloom-report/weekly")

    assert response.status_code == 200
    body = response.json()
    assert body["period"] == {"start_date": "2026-04-19", "end_date": "2026-04-25"}
    assert body["stats"]["gigs_completed"] == 2
    assert body["highlights"][0]["title"] == "Family win"
    assert body["savings_insight"] == "EUR 12.50 earned means EUR 6.25 could go straight into savings this week."
    assert body["conversation_starter"] == "Which reward felt most worth the effort this week?"
    assert body["mode"] == "fake_local"
    assert body["fallback_mode"] is False
