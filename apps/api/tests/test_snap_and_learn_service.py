import base64

from app.errors import AppError
from app.dependencies import get_snap_and_learn_service
from app.integrations.fake_payment_client import FakePaymentClient
from app.integrations.lmstudio_client import LMStudioVisionClient
from app.integrations.unconfigured_verification_client import UnconfiguredVerificationClient
from app.repositories.photo_repository import PhotoRepository
from app.repositories.state_repository import StateRepository
from app.settings import get_settings
from app.services.payment_service import PaymentService
from app.services.snap_and_learn_service import SnapAndLearnService


def image_data_url(payload: bytes = b"fake-image") -> str:
    encoded = base64.b64encode(payload).decode()
    return f"data:image/png;base64,{encoded}"


class FakeSnapAndLearnClient:
    mode = "fake"

    def analyze(self, *, image_base64: str) -> dict:
        return {
            "item_name": "LEGO City Race Car",
            "estimated_price": {"amount": "34.99", "currency": "EUR"},
            "confidence": 0.88,
            "reasoning_summary": "Fake analysis recognized a toy car set for the demo.",
            "raw_provider": "fake",
            "raw_model": "fake-snap-v1",
        }


class BrokenSnapAndLearnClient:
    mode = "real"

    def analyze(self, *, image_base64: str) -> dict:
        raise RuntimeError("vision unavailable")


class RealSnapAndLearnClient:
    mode = "real"

    def analyze(self, *, image_base64: str) -> dict:
        return {
            "item_name": "Blue Bicycle Helmet",
            "estimated_price": {"amount": "29.95", "currency": "EUR"},
            "confidence": 0.84,
            "reasoning_summary": "Provider-backed analysis recognized a bike helmet.",
            "raw_provider": "lmstudio",
            "raw_model": "qwen2.5-vl",
        }


class RealPaymentClient(FakePaymentClient):
    mode = "real"

    def get_kid_balance(self, state=None):
        return {"amount": "22.50", "currency": "EUR", "source": "bunq"}


def make_service(tmp_path, analysis_client, *, allow_fallback: bool = False) -> SnapAndLearnService:
    return SnapAndLearnService(
        state_repository=StateRepository(tmp_path / "state.json"),
        photo_repository=PhotoRepository(tmp_path / "uploads"),
        analysis_client=analysis_client,
        payment_service=PaymentService(FakePaymentClient()),
        allow_ai_fallback=allow_fallback,
    )


def make_service_with_payment(tmp_path, analysis_client, payment_client) -> SnapAndLearnService:
    return SnapAndLearnService(
        state_repository=StateRepository(tmp_path / "state.json"),
        photo_repository=PhotoRepository(tmp_path / "uploads"),
        analysis_client=analysis_client,
        payment_service=PaymentService(payment_client),
    )


def test_snap_and_learn_returns_analysis_and_gigs_needed(tmp_path):
    service = make_service(tmp_path, FakeSnapAndLearnClient())

    result = service.analyze(image_data_url(b"item-photo"))

    assert result["analysis"]["item_name"] == "LEGO City Race Car"
    assert result["analysis"]["estimated_price"] == {"amount": "34.99", "currency": "EUR"}
    assert result["analysis"]["gigs_needed"] == 3
    assert result["analysis"]["suggested_goal"].startswith("Save for LEGO City Race Car")
    assert result["kid_balance"]["amount"] == "22.50"
    assert result["mode"] == "fake_local"
    assert result["fallback_mode"] is False


def test_snap_and_learn_can_fallback_when_explicitly_enabled(tmp_path):
    service = make_service(tmp_path, BrokenSnapAndLearnClient(), allow_fallback=True)

    result = service.analyze(image_data_url(b"item-photo"))

    assert result["analysis"]["item_name"] == "Mystery item"
    assert result["analysis"]["estimated_price"]["currency"] == "EUR"
    assert result["analysis"]["gigs_needed"] >= 1
    assert result["mode"] == "ai_fallback"
    assert result["fallback_mode"] is True


def test_snap_and_learn_can_fallback_when_ai_is_unconfigured(tmp_path):
    service = make_service(
        tmp_path,
        UnconfiguredVerificationClient(provider="lmstudio"),
        allow_fallback=True,
    )

    result = service.analyze(image_data_url(b"item-photo"))

    assert result["analysis"]["item_name"] == "Mystery item"
    assert result["mode"] == "ai_fallback"
    assert result["fallback_mode"] is True


def test_snap_and_learn_raises_retryable_error_without_fallback(tmp_path):
    service = make_service(tmp_path, BrokenSnapAndLearnClient(), allow_fallback=False)

    try:
        service.analyze(image_data_url(b"item-photo"))
    except AppError as exc:
        assert exc.code == "analysis_failed"
        assert exc.status_code == 502
        assert exc.retryable is True
    else:
        raise AssertionError("Expected AppError for failed analysis without fallback")


def test_snap_and_learn_reports_fake_payment_mode_for_provider_backed_analysis(tmp_path):
    service = make_service(tmp_path, RealSnapAndLearnClient(), allow_fallback=False)

    result = service.analyze(image_data_url(b"item-photo"))

    assert result["analysis"]["item_name"] == "Blue Bicycle Helmet"
    assert result["analysis"]["estimated_price"] == {"amount": "29.95", "currency": "EUR"}
    assert result["mode"] == "fake_local"
    assert result["ai_mode"] == "real"
    assert result["payment_mode"] == "fake_local"
    assert result["fallback_mode"] is False


def test_snap_and_learn_reports_fake_ai_mode_for_fake_analysis_with_real_payment(tmp_path):
    service = make_service_with_payment(tmp_path, FakeSnapAndLearnClient(), RealPaymentClient())

    result = service.analyze(image_data_url(b"item-photo"))

    assert result["mode"] == "fake_ai"
    assert result["ai_mode"] == "fake"
    assert result["payment_mode"] == "real"
    assert result["fallback_mode"] is False


def test_dependency_selects_lmstudio_client_for_snap_and_learn(monkeypatch, tmp_path):
    state_dir = tmp_path / "state"
    upload_dir = tmp_path / "uploads"
    state_dir.mkdir()
    upload_dir.mkdir()

    monkeypatch.setenv("BLOOM_AI_PROVIDER", "lmstudio")
    monkeypatch.setenv("BLOOM_LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
    monkeypatch.setenv("BLOOM_LMSTUDIO_MODEL", "qwen2.5-vl")
    monkeypatch.setenv("BLOOM_USE_FAKE_BUNQ", "true")
    monkeypatch.setenv("BLOOM_STATE_PATH", str(state_dir / "state.json"))
    monkeypatch.setenv("BLOOM_UPLOAD_DIR", str(upload_dir))

    get_settings.cache_clear()
    get_snap_and_learn_service.cache_clear()

    service = get_snap_and_learn_service()

    assert isinstance(service.analysis_client, LMStudioVisionClient)

    get_settings.cache_clear()
    get_snap_and_learn_service.cache_clear()


def test_dependency_selects_unconfigured_client_for_snap_and_learn_when_ai_is_unconfigured(monkeypatch, tmp_path):
    state_dir = tmp_path / "state"
    upload_dir = tmp_path / "uploads"
    state_dir.mkdir()
    upload_dir.mkdir()

    monkeypatch.setenv("BLOOM_AI_PROVIDER", "lmstudio")
    monkeypatch.setenv("BLOOM_LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
    monkeypatch.setenv("BLOOM_LMSTUDIO_MODEL", "")
    monkeypatch.setenv("BLOOM_USE_FAKE_BUNQ", "true")
    monkeypatch.setenv("BLOOM_STATE_PATH", str(state_dir / "state.json"))
    monkeypatch.setenv("BLOOM_UPLOAD_DIR", str(upload_dir))

    get_settings.cache_clear()
    get_snap_and_learn_service.cache_clear()

    service = get_snap_and_learn_service()

    assert isinstance(service.analysis_client, UnconfiguredVerificationClient)

    get_settings.cache_clear()
    get_snap_and_learn_service.cache_clear()
