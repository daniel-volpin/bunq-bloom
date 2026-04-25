import pytest

from app.integrations.lmstudio_client import LMStudioVisionClient


class StubResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("http error")

    def json(self):
        return self._payload


class StubHttpClient:
    def __init__(self, response: StubResponse | None = None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.calls = []

    def post(self, url, json, headers, timeout):
        self.calls.append({"url": url, "json": json, "headers": headers, "timeout": timeout})
        if self.error:
            raise self.error
        return self.response


def _gig() -> dict:
    return {
        "id": "gig_001",
        "title": "Clean bedroom",
        "description": "Make your room tidy",
        "verification_checklist": ["bed made", "floor clear"],
    }


def _photo(tmp_path, name: str) -> dict:
    path = tmp_path / name
    path.write_bytes(b"fake-image")
    return {
        "id": f"photo_{name}",
        "gig_id": "gig_001",
        "kind": "before",
        "content_type": "image/png",
        "storage_ref": str(path),
    }


def test_verify_parses_lmstudio_json_response(tmp_path):
    http = StubHttpClient(
        response=StubResponse(
            {
                "model": "qwen3.5-9b-mlx",
                "choices": [
                    {
                        "message": {
                            "content": '{"approved": true, "confidence": 0.9, "tags": ["bed made"], '
                            '"message_for_kid": "Great job tidying up.", '
                            '"reasoning_summary": "Bed is made and room looks improved."}'
                        }
                    }
                ],
            }
        )
    )
    client = LMStudioVisionClient(
        base_url="http://127.0.0.1:1234/v1",
        model="qwen3.5-9b-mlx",
        http_client=http,
    )

    result = client.verify(
        gig=_gig(),
        before_photo=_photo(tmp_path, "before.png"),
        after_photo=_photo(tmp_path, "after.png"),
    )

    assert result["approved"] is True
    assert result["confidence"] == 0.9
    assert result["raw_provider"] == "lmstudio"
    assert result["raw_model"] == "qwen3.5-9b-mlx"
    assert http.calls[0]["url"] == "http://127.0.0.1:1234/v1/chat/completions"
    assert http.calls[0]["json"]["response_format"]["type"] == "json_schema"


def test_verify_raises_on_invalid_json(tmp_path):
    http = StubHttpClient(
        response=StubResponse(
            {
                "model": "qwen3.5-9b-mlx",
                "choices": [{"message": {"content": "not-json"}}],
            }
        )
    )
    client = LMStudioVisionClient(
        base_url="http://127.0.0.1:1234/v1",
        model="qwen3.5-9b-mlx",
        http_client=http,
    )

    with pytest.raises(RuntimeError, match="invalid JSON"):
        client.verify(
            gig=_gig(),
            before_photo=_photo(tmp_path, "before.png"),
            after_photo=_photo(tmp_path, "after.png"),
        )


def test_verify_raises_on_transport_error(tmp_path):
    http = StubHttpClient(error=RuntimeError("connection refused"))
    client = LMStudioVisionClient(
        base_url="http://127.0.0.1:1234/v1",
        model="qwen3.5-9b-mlx",
        http_client=http,
    )

    with pytest.raises(RuntimeError, match="LM Studio request failed"):
        client.verify(
            gig=_gig(),
            before_photo=_photo(tmp_path, "before.png"),
            after_photo=_photo(tmp_path, "after.png"),
        )


def test_verify_parses_reasoning_content_when_content_is_empty(tmp_path):
    http = StubHttpClient(
        response=StubResponse(
            {
                "model": "qwen3.5-9b-mlx",
                "choices": [
                    {
                        "message": {
                            "content": "",
                            "reasoning_content": '{"approved": false, "confidence": 0.4, "tags": ["bed made"], '
                            '"message_for_kid": "The floor still needs work.", '
                            '"reasoning_summary": "The room improved, but the checklist is not complete."}'
                        }
                    }
                ],
            }
        )
    )
    client = LMStudioVisionClient(
        base_url="http://127.0.0.1:1234/v1",
        model="qwen3.5-9b-mlx",
        http_client=http,
    )

    result = client.verify(
        gig=_gig(),
        before_photo=_photo(tmp_path, "before.png"),
        after_photo=_photo(tmp_path, "after.png"),
    )

    assert result["approved"] is False
    assert result["confidence"] == 0.4