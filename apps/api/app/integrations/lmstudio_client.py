import base64
import json
from pathlib import Path
from typing import Any

import requests
from pydantic import BaseModel, Field, ValidationError

from app.models.domain import new_id
from app.models.verification import VerificationResultModel


class _LMStudioVerificationPayload(BaseModel):
    approved: bool
    confidence: float = Field(ge=0, le=1)
    tags: list[str]
    message_for_kid: str = Field(min_length=1, max_length=300)
    reasoning_summary: str = Field(min_length=1, max_length=1000)


class LMStudioVisionClient:
    mode = "real"

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str | None = None,
        timeout_seconds: int = 45,
        http_client: Any | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.http_client = http_client or requests

    def verify(self, *, gig: dict, before_photo: dict, after_photo: dict) -> dict:
        payload = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 350,
            "response_format": self._response_format(),
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self._prompt(gig)},
                        self._image_block(before_photo),
                        self._image_block(after_photo),
                    ],
                }
            ],
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = self.http_client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            body = response.json()
        except Exception as exc:
            raise RuntimeError("LM Studio request failed.") from exc

        content = self._extract_message_content(body)
        parsed = self._parse_payload(content)
        tags = [str(tag).strip() for tag in parsed.tags if str(tag).strip()]

        return VerificationResultModel(
            id=new_id("verif"),
            gig_id=gig["id"],
            approved=parsed.approved,
            confidence=parsed.confidence,
            tags=tags,
            message_for_kid=parsed.message_for_kid,
            reasoning_summary=parsed.reasoning_summary,
            raw_provider="lmstudio",
            raw_model=str(body.get("model") or self.model),
        ).model_dump()

    def _extract_message_content(self, body: dict[str, Any]) -> str:
        try:
            message = body["choices"][0]["message"]
        except Exception as exc:
            raise RuntimeError("LM Studio returned an invalid response shape.") from exc

        content = self._extract_text_value(message.get("content"))
        if content:
            return content

        reasoning_content = self._extract_text_value(message.get("reasoning_content"))
        if reasoning_content:
            return reasoning_content

        raise RuntimeError("LM Studio returned an invalid content format.")

    def _extract_text_value(self, content: Any) -> str | None:
        if isinstance(content, str):
            text = content.strip()
            if not text:
                return None
            return text

        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    value = item.get("text")
                    if value:
                        parts.append(str(value))
            combined = "\n".join(parts).strip()
            if combined:
                return combined

        return None

    def _parse_payload(self, content: str) -> _LMStudioVerificationPayload:
        json_text = self._extract_json_text(content)
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("LM Studio returned invalid JSON.") from exc

        try:
            return _LMStudioVerificationPayload.model_validate(payload)
        except ValidationError as exc:
            raise RuntimeError("LM Studio response is missing required verification fields.") from exc

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
            "type": "image_url",
            "image_url": {
                "url": f"data:{content_type};base64,{encoded}",
            },
        }

    def _response_format(self) -> dict[str, Any]:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "verification_result",
                "schema": {
                    "type": "object",
                    "properties": {
                        "approved": {"type": "boolean"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "message_for_kid": {"type": "string"},
                        "reasoning_summary": {"type": "string"},
                    },
                    "required": [
                        "approved",
                        "confidence",
                        "tags",
                        "message_for_kid",
                        "reasoning_summary",
                    ],
                    "additionalProperties": False,
                },
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