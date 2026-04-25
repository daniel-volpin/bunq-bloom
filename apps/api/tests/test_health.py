import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.settings import get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def make_client(monkeypatch, tmp_path, *, ai_provider: str = "lmstudio", fake_bunq: bool = True) -> TestClient:
    state_dir = tmp_path / "state"
    upload_dir = tmp_path / "uploads"
    state_dir.mkdir()
    upload_dir.mkdir()

    monkeypatch.setenv("BLOOM_AI_PROVIDER", ai_provider)
    monkeypatch.setenv("BLOOM_LMSTUDIO_MODEL", "qwen3.5-9b-mlx")
    monkeypatch.setenv("BLOOM_USE_FAKE_BUNQ", str(fake_bunq).lower())
    monkeypatch.setenv("BLOOM_STATE_PATH", str(state_dir / "state.json"))
    monkeypatch.setenv("BLOOM_UPLOAD_DIR", str(upload_dir))
    monkeypatch.setenv("BLOOM_BUNQ_TOOLKIT_PATH", str(tmp_path / "missing-toolkit"))
    get_settings.cache_clear()

    return TestClient(create_app())


def test_health_reports_lmstudio_integrations_and_ready_local_paths(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)

    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["readiness_status"] == "ready"
    assert body["integrations"]["ai"] == {
        "mode": "real",
        "ready": True,
        "status": "configured",
        "missing_config": [],
    }
    assert body["integrations"]["bunq"] == {
        "mode": "fake",
        "ready": True,
        "status": "configured",
        "missing_config": [],
    }
    assert body["integrations"]["state"]["status"] == "ok"
    assert body["integrations"]["state"]["ready"] is True
    assert body["integrations"]["uploads"]["status"] == "ok"
    assert body["integrations"]["uploads"]["ready"] is True


def test_health_reports_real_integration_missing_config_codes_without_values(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret-anthropic-key")
    monkeypatch.setenv("BUNQ_API_KEY", "secret-bunq-key")
    client = make_client(monkeypatch, tmp_path, ai_provider="anthropic", fake_bunq=False)

    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["readiness_status"] == "not_ready"
    assert body["integrations"]["ai"] == {
        "mode": "real",
        "ready": True,
        "status": "configured",
        "missing_config": [],
    }
    assert body["integrations"]["bunq"]["mode"] == "real"
    assert body["integrations"]["bunq"]["ready"] is False
    assert body["integrations"]["bunq"]["status"] == "not_configured"
    assert body["integrations"]["bunq"]["missing_config"] == [
        "bunq_parent_account_id_missing",
        "bunq_kid_account_id_missing",
        "bunq_toolkit_client_missing",
    ]
    assert "secret-anthropic-key" not in response.text
    assert "secret-bunq-key" not in response.text


def test_health_reports_state_and_upload_readiness_failures(monkeypatch, tmp_path):
    upload_path = tmp_path / "upload-file"
    upload_path.write_text("not a directory", encoding="utf-8")

    monkeypatch.setenv("BLOOM_AI_PROVIDER", "lmstudio")
    monkeypatch.setenv("BLOOM_LMSTUDIO_MODEL", "qwen3.5-9b-mlx")
    monkeypatch.setenv("BLOOM_USE_FAKE_BUNQ", "true")
    state_parent_file = tmp_path / "state-parent-file"
    state_parent_file.write_text("not a directory", encoding="utf-8")

    monkeypatch.setenv("BLOOM_STATE_PATH", str(state_parent_file / "state.json"))
    monkeypatch.setenv("BLOOM_UPLOAD_DIR", str(upload_path))
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["readiness_status"] == "not_ready"
    assert body["integrations"]["state"]["status"] == "not_ready"
    assert body["integrations"]["state"]["ready"] is False
    assert body["integrations"]["state"]["missing_config"] == ["state_path_parent_not_directory"]
    assert body["integrations"]["uploads"]["status"] == "not_ready"
    assert body["integrations"]["uploads"]["ready"] is False
    assert body["integrations"]["uploads"]["missing_config"] == ["upload_dir_not_directory"]


def test_health_treats_missing_but_creatable_local_dirs_as_ready(monkeypatch, tmp_path):
    monkeypatch.setenv("BLOOM_AI_PROVIDER", "lmstudio")
    monkeypatch.setenv("BLOOM_LMSTUDIO_MODEL", "qwen3.5-9b-mlx")
    monkeypatch.setenv("BLOOM_USE_FAKE_BUNQ", "true")
    monkeypatch.setenv("BLOOM_STATE_PATH", str(tmp_path / "new-state-dir" / "state.json"))
    monkeypatch.setenv("BLOOM_UPLOAD_DIR", str(tmp_path / "new-uploads"))
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["readiness_status"] == "ready"
    assert body["integrations"]["state"]["status"] == "ok"
    assert body["integrations"]["state"]["ready"] is True
    assert body["integrations"]["state"]["missing_config"] == []
    assert body["integrations"]["uploads"]["status"] == "ok"
    assert body["integrations"]["uploads"]["ready"] is True
    assert body["integrations"]["uploads"]["creatable"] is True


def test_health_reports_local_fake_ai_mode_when_lmstudio_model_is_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("BLOOM_AI_PROVIDER", "lmstudio")
    monkeypatch.setenv("BLOOM_LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
    monkeypatch.delenv("BLOOM_LMSTUDIO_MODEL", raising=False)
    monkeypatch.setenv("BLOOM_USE_FAKE_BUNQ", "true")
    monkeypatch.setenv("BLOOM_STATE_PATH", str(tmp_path / "state" / "state.json"))
    monkeypatch.setenv("BLOOM_UPLOAD_DIR", str(tmp_path / "uploads"))
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["readiness_status"] == "not_ready"
    assert body["integrations"]["ai"]["mode"] == "real"
    assert body["integrations"]["ai"]["ready"] is False
    assert body["integrations"]["ai"]["status"] == "not_configured"
    assert body["integrations"]["ai"]["missing_config"] == ["lmstudio_model_missing"]
