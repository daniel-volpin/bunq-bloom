import base64
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.integrations.json_response import extract_json_text
from app.integrations.prompt_templates import (
    build_snap_and_learn_prompt,
    build_verification_prompt,
    build_weekly_report_prompt,
)
from app.models.domain import new_id
from app.models.verification import VerificationResultModel


class _ClaudeVerificationPayload(BaseModel):
    approved: bool
    confidence: float = Field(ge=0, le=1)
    tags: list[str]
    message_for_kid: str = Field(min_length=1, max_length=300)
    reasoning_summary: str = Field(min_length=1, max_length=1000)


class _ClaudeSnapAndLearnPayload(BaseModel):
    item_name: str = Field(min_length=1, max_length=200)
    estimated_price: str = Field(min_length=1, max_length=20)
    currency: str = Field(min_length=3, max_length=3)
    confidence: float = Field(ge=0, le=1)
    reasoning_summary: str = Field(min_length=1, max_length=1000)


class _ClaudeWeeklyReportPayload(BaseModel):
    highlights: list[dict[str, str]]
    savings_insight: str = Field(min_length=1, max_length=500)
    conversation_starter: str = Field(min_length=1, max_length=300)


class ClaudeVisionClient:
    mode = "real"

    def __init__(
        self,
        *,
        api_key: str,
        anthropic_client: Any | None = None,
        model: str = "claude-sonnet-4-6",
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

    def analyze(self, *, image_base64: str) -> dict:
        response = self._get_client().messages.create(
            model=self.model,
            max_tokens=250,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self._snap_prompt()},
                        self._inline_image_block(image_base64),
                    ],
                }
            ],
        )

        text = self._extract_text(response)
        payload = self._parse_snap_payload(text)
        return {
            "item_name": payload.item_name,
            "estimated_price": {
                "amount": payload.estimated_price,
                "currency": payload.currency,
            },
            "confidence": payload.confidence,
            "reasoning_summary": payload.reasoning_summary,
            "raw_provider": "anthropic",
            "raw_model": str(getattr(response, "model", self.model)),
        }

    def generate_weekly_report(self, *, report_context: dict) -> dict:
        response = self._get_client().messages.create(
            model=self.model,
            max_tokens=350,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self._weekly_report_prompt(report_context)},
                    ],
                }
            ],
        )

        text = self._extract_text(response)
        payload = self._parse_weekly_report_payload(text)
        return {
            "highlights": payload.highlights,
            "savings_insight": payload.savings_insight,
            "conversation_starter": payload.conversation_starter,
            "raw_provider": "anthropic",
            "raw_model": str(getattr(response, "model", self.model)),
        }

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

    def _inline_image_block(self, image_base64: str) -> dict[str, Any]:
        content_type, encoded = self._split_data_url(image_base64)
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": content_type,
                "data": encoded,
            },
        }

    def _prompt(self, gig: dict) -> str:
        return build_verification_prompt(gig)

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
        json_text = extract_json_text(content)
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Claude returned invalid JSON.") from exc

        try:
            return _ClaudeVerificationPayload.model_validate(payload)
        except ValidationError as exc:
            raise RuntimeError("Claude response is missing required verification fields.") from exc

    def _parse_snap_payload(self, content: str) -> _ClaudeSnapAndLearnPayload:
        json_text = extract_json_text(content)
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Claude returned invalid JSON.") from exc

        try:
            return _ClaudeSnapAndLearnPayload.model_validate(payload)
        except ValidationError as exc:
            raise RuntimeError("Claude response is missing required Snap & Learn fields.") from exc

    def _parse_weekly_report_payload(self, content: str) -> _ClaudeWeeklyReportPayload:
        json_text = extract_json_text(content)
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Claude returned invalid JSON.") from exc

        try:
            return _ClaudeWeeklyReportPayload.model_validate(payload)
        except ValidationError as exc:
            raise RuntimeError("Claude response is missing required weekly report fields.") from exc

    def _split_data_url(self, image_base64: str) -> tuple[str, str]:
        if not image_base64.startswith("data:") or ";base64," not in image_base64:
            raise RuntimeError("Image must be a base64 data URL.")
        header, encoded = image_base64.split(";base64,", 1)
        return header.removeprefix("data:"), encoded

    def _snap_prompt(self) -> str:
        return build_snap_and_learn_prompt()

    def _weekly_report_prompt(self, report_context: dict) -> str:
        return build_weekly_report_prompt(report_context)
