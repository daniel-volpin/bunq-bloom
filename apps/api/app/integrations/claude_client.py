import base64
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.models.domain import new_id
from app.models.verification import VerificationResultModel


class _ClaudeVerificationPayload(BaseModel):
    approved: bool
    confidence: float = Field(ge=0, le=1)
    tags: list[str]
    message_for_kid: str = Field(min_length=1, max_length=300)
    reasoning_summary: str = Field(min_length=1, max_length=1000)


class ClaudeVisionClient:
    mode = "real"

    def __init__(
        self,
        *,
        api_key: str,
        anthropic_client: Any | None = None,
        model: str = "claude-3-5-sonnet-latest",
    ):
        self.api_key = api_key
        self.model = model
        self._client = anthropic_client

    def verify(self, *, gig: dict, before_photo: dict, after_photo: dict) -> dict:
        response = self._get_client().messages.create(
            model=self.model,
            max_tokens=350,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self._prompt(gig)},
                        self._image_block(before_photo),
                        self._image_block(after_photo),
                    ],
                }
            ],
        )

        text = self._extract_text(response)
        payload = self._parse_payload(text)
        tags = [str(tag).strip() for tag in payload.tags if str(tag).strip()]

        return VerificationResultModel(
            id=new_id("verif"),
            gig_id=gig["id"],
            approved=payload.approved,
            confidence=payload.confidence,
            tags=tags,
            message_for_kid=payload.message_for_kid,
            reasoning_summary=payload.reasoning_summary,
            raw_provider="anthropic",
            raw_model=str(getattr(response, "model", self.model)),
        ).model_dump()

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client

        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise RuntimeError("Anthropic SDK is not installed.") from exc

        self._client = Anthropic(api_key=self.api_key)
        return self._client

    def _image_block(self, photo: dict) -> dict[str, Any]:
        storage_ref = photo.get("storage_ref")
        content_type = photo.get("content_type")
        if not storage_ref or not content_type:
            raise RuntimeError("Photo metadata is incomplete for AI verification.")

        path = Path(str(storage_ref))
        if not path.exists() or not path.is_file():
            raise RuntimeError("Photo file is missing for AI verification.")

        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": str(content_type),
                "data": encoded,
            },
        }

    def _prompt(self, gig: dict) -> str:
        title = str(gig.get("title") or "").strip()
        description = str(gig.get("description") or "").strip()
        checklist = gig.get("verification_checklist") or []
        checklist_items = [str(item).strip() for item in checklist if str(item).strip()]
        checklist_text = "\n".join(f"- {item}" for item in checklist_items) or "- task improved"

        return (
            "You are verifying a kid's completed gig using BEFORE and AFTER photos.\n"
            "Compare both photos against the gig details and checklist.\n"
            "Be strict, fair, and concise.\n\n"
            "Return JSON only with this exact schema:\n"
            "{\n"
            '  "approved": boolean,\n'
            '  "confidence": number between 0 and 1,\n'
            '  "tags": ["short tag"],\n'
            '  "message_for_kid": "short encouraging sentence",\n'
            '  "reasoning_summary": "short reason for parent/backend"\n'
            "}\n\n"
            "Rules:\n"
            "- If required evidence is missing, set approved to false.\n"
            "- Keep tags short and relevant to checklist evidence.\n"
            "- Do not include markdown, prose, or extra keys.\n\n"
            f"Gig title: {title}\n"
            f"Gig description: {description}\n"
            f"Checklist:\n{checklist_text}\n"
        )

    def _extract_text(self, response: Any) -> str:
        parts = []
        for block in getattr(response, "content", []):
            text = getattr(block, "text", None)
            if text:
                parts.append(str(text))

        combined = "\n".join(parts).strip()
        if not combined:
            raise RuntimeError("Claude returned an empty response.")
        return combined

    def _parse_payload(self, content: str) -> _ClaudeVerificationPayload:
        json_text = self._extract_json_text(content)
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Claude returned invalid JSON.") from exc

        try:
            return _ClaudeVerificationPayload.model_validate(payload)
        except ValidationError as exc:
            raise RuntimeError("Claude response is missing required verification fields.") from exc

    def _extract_json_text(self, content: str) -> str:
        stripped = content.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if len(lines) >= 3 and lines[-1].strip() == "```":
                body = lines[1:-1]
                if body and body[0].strip().lower() == "json":
                    body = body[1:]
                stripped = "\n".join(body).strip()
        return stripped