from types import SimpleNamespace

import pytest

from app.integrations.claude_client import ClaudeVisionClient


class StubMessagesAPI:
    def __init__(self, response=None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


class StubAnthropicClient:
    def __init__(self, messages_api: StubMessagesAPI):
        self.messages = messages_api


def _gig() -> dict:
    return {
        "id": "gig_001",
        "title": "Clean bedroom",
        "description": "Make the room tidy before dinner",
        "verification_checklist": ["bed made", "floor clear", "desk tidy"],
    }


def _photo(tmp_path, filename: str, content_type: str = "image/png") -> dict:
    path = tmp_path / filename
    path.write_bytes(b"fake-image")
    return {
        "id": f"photo_{filename}",
        "gig_id": "gig_001",
        "kind": "before",
        "content_type": content_type,
        "storage_ref": str(path),
    }


def _response(text: str, *, model: str = "claude-3-5-sonnet-20241022"):
    return SimpleNamespace(
        model=model,
        content=[SimpleNamespace(type="text", text=text)],
    )


def test_verify_parses_claude_json_and_returns_backend_schema(tmp_path):
    messages_api = StubMessagesAPI(
        response=_response(
            '{"approved": true, "confidence": 0.94, "tags": ["bed made", "desk tidy"], '
            '"message_for_kid": "Nice work. Your room looks tidy.", '
            '"reasoning_summary": "Checklist items are visible in the after photo."}'
        )
    )
    client = ClaudeVisionClient(
        api_key="test-key",
        anthropic_client=StubAnthropicClient(messages_api),
    )

    result = client.verify(
        gig=_gig(),
        before_photo=_photo(tmp_path, "before.png"),
        after_photo=_photo(tmp_path, "after.png"),
    )

    assert result["gig_id"] == "gig_001"
    assert result["approved"] is True
    assert result["confidence"] == 0.94
    assert result["tags"] == ["bed made", "desk tidy"]
    assert result["raw_provider"] == "anthropic"
    assert result["raw_model"] == "claude-3-5-sonnet-20241022"

    call = messages_api.calls[0]
    assert call["model"] == "claude-3-5-sonnet-latest"
    assert call["temperature"] == 0
    assert call["max_tokens"] == 350
    prompt_text = call["messages"][0]["content"][0]["text"]
    assert "Clean bedroom" in prompt_text
    assert "Make the room tidy before dinner" in prompt_text
    assert "- bed made" in prompt_text
    assert call["messages"][0]["content"][1]["type"] == "image"
    assert call["messages"][0]["content"][2]["type"] == "image"


def test_verify_raises_on_invalid_json_output(tmp_path):
    messages_api = StubMessagesAPI(response=_response("not-json"))
    client = ClaudeVisionClient(
        api_key="test-key",
        anthropic_client=StubAnthropicClient(messages_api),
    )

    with pytest.raises(RuntimeError, match="invalid JSON"):
        client.verify(
            gig=_gig(),
            before_photo=_photo(tmp_path, "before.png"),
            after_photo=_photo(tmp_path, "after.png"),
        )


def test_verify_raises_when_required_fields_are_missing(tmp_path):
    messages_api = StubMessagesAPI(
        response=_response(
            '{"approved": true, "tags": ["bed made"], '
            '"message_for_kid": "Nice.", "reasoning_summary": "Looks better."}'
        )
    )
    client = ClaudeVisionClient(
        api_key="test-key",
        anthropic_client=StubAnthropicClient(messages_api),
    )

    with pytest.raises(RuntimeError, match="missing required verification fields"):
        client.verify(
            gig=_gig(),
            before_photo=_photo(tmp_path, "before.png"),
            after_photo=_photo(tmp_path, "after.png"),
        )


def test_verify_raises_on_missing_photo_file(tmp_path):
    messages_api = StubMessagesAPI(response=_response("{}"))
    client = ClaudeVisionClient(
        api_key="test-key",
        anthropic_client=StubAnthropicClient(messages_api),
    )

    missing_photo = {
        "id": "photo_missing",
        "gig_id": "gig_001",
        "kind": "before",
        "content_type": "image/png",
        "storage_ref": str(tmp_path / "missing.png"),
    }

    with pytest.raises(RuntimeError, match="Photo file is missing"):
        client.verify(
            gig=_gig(),
            before_photo=missing_photo,
            after_photo=_photo(tmp_path, "after.png"),
        )