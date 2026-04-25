import pytest

from app.dependencies import get_gig_service
from app.integrations.claude_client import ClaudeVisionClient
from app.integrations.fake_verification_client import FakeVerificationClient
from app.integrations.lmstudio_client import LMStudioVisionClient
from app.integrations.unconfigured_verification_client import UnconfiguredVerificationClient
from app.settings import get_settings


@pytest.fixture(autouse=True)
def clear_caches():
    get_settings.cache_clear()
    get_gig_service.cache_clear()
    yield
    get_settings.cache_clear()
    get_gig_service.cache_clear()


def _configure_common(monkeypatch, tmp_path):
    monkeypatch.setenv("BLOOM_STATE_PATH", str(tmp_path / "state.json"))
    monkeypatch.setenv("BLOOM_UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("BLOOM_USE_FAKE_BUNQ", "true")


def test_uses_anthropic_client_when_provider_is_anthropic_and_key_present(monkeypatch, tmp_path):
    _configure_common(monkeypatch, tmp_path)
    monkeypatch.setenv("BLOOM_AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")

    service = get_gig_service()

    assert isinstance(service.verification_client, ClaudeVisionClient)


def test_uses_fake_client_when_anthropic_key_is_missing_in_local_fake_mode(monkeypatch, tmp_path):
    _configure_common(monkeypatch, tmp_path)
    monkeypatch.setenv("BLOOM_AI_PROVIDER", "anthropic")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    service = get_gig_service()

    assert isinstance(service.verification_client, FakeVerificationClient)


def test_uses_lmstudio_client_when_provider_is_lmstudio(monkeypatch, tmp_path):
    _configure_common(monkeypatch, tmp_path)
    monkeypatch.setenv("BLOOM_AI_PROVIDER", "lmstudio")
    monkeypatch.setenv("BLOOM_LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
    monkeypatch.setenv("BLOOM_LMSTUDIO_MODEL", "qwen3.5-9b-mlx")

    service = get_gig_service()

    assert isinstance(service.verification_client, LMStudioVisionClient)


def test_uses_fake_client_when_lmstudio_model_is_missing_in_local_fake_mode(monkeypatch, tmp_path):
    _configure_common(monkeypatch, tmp_path)
    monkeypatch.setenv("BLOOM_AI_PROVIDER", "lmstudio")
    monkeypatch.setenv("BLOOM_LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
    monkeypatch.delenv("BLOOM_LMSTUDIO_MODEL", raising=False)

    service = get_gig_service()

    assert isinstance(service.verification_client, FakeVerificationClient)


def test_lmstudio_provider_does_not_fall_through_to_anthropic(monkeypatch, tmp_path):
    _configure_common(monkeypatch, tmp_path)
    monkeypatch.setenv("BLOOM_AI_PROVIDER", "lmstudio")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.delenv("BLOOM_LMSTUDIO_MODEL", raising=False)

    service = get_gig_service()

    assert isinstance(service.verification_client, FakeVerificationClient)


def test_uses_unconfigured_client_when_missing_ai_config_in_real_mode(monkeypatch, tmp_path):
    _configure_common(monkeypatch, tmp_path)
    monkeypatch.setenv("BLOOM_AI_PROVIDER", "lmstudio")
    monkeypatch.setenv("BLOOM_USE_FAKE_BUNQ", "false")
    monkeypatch.setenv("BUNQ_API_KEY", "test-bunq-key")
    monkeypatch.setenv("BUNQ_PARENT_ACCOUNT_ID", "parent-account")
    monkeypatch.setenv("BUNQ_KID_ACCOUNT_ID", "kid-account")
    monkeypatch.delenv("BLOOM_LMSTUDIO_MODEL", raising=False)

    service = get_gig_service()

    assert isinstance(service.verification_client, UnconfiguredVerificationClient)