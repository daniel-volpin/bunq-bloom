import base64
import json
from pathlib import Path
from typing import Any

import requests
from pydantic import BaseModel, Field, ValidationError

from app.integrations.json_response import extract_json_text
from app.integrations.prompt_templates import (
    build_snap_and_learn_prompt,
    build_verification_prompt,
    build_weekly_report_prompt,
)
from app.models.domain import new_id
from app.models.verification import VerificationResultModel


class _LMStudioVerificationPayload(BaseModel):
    approved: bool
    confidence: float = Field(ge=0, le=1)
    tags: list[str]
    message_for_kid: str = Field(min_length=1, max_length=300)
    reasoning_summary: str = Field(min_length=1, max_length=1000)


class _LMStudioSnapAndLearnPayload(BaseModel):
    item_name: str = Field(min_length=1, max_length=200)
    estimated_price: str = Field(min_length=1, max_length=20)
    currency: str = Field(min_length=3, max_length=3)
    confidence: float = Field(ge=0, le=1)
    reasoning_summary: str = Field(min_length=1, max_length=1000)


class _LMStudioWeeklyReportPayload(BaseModel):
    highlights: list[dict[str, str]]
    savings_insight: str = Field(min_length=1, max_length=500)
    conversation_starter: str = Field(min_length=1, max_length=300)


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

        body = self._post_json(payload)

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

    def analyze(self, *, image_base64: str) -> dict:
        payload = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 250,
            "response_format": self._snap_response_format(),
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self._snap_prompt()},
                        self._inline_image_block(image_base64),
                    ],
                }
            ],
        }

        body = self._post_json(payload)

        content = self._extract_message_content(body)
        parsed = self._parse_snap_payload(content)
        return {
            "item_name": parsed.item_name,
            "estimated_price": {
                "amount": parsed.estimated_price,
                "currency": parsed.currency,
            },
            "confidence": parsed.confidence,
            "reasoning_summary": parsed.reasoning_summary,
            "raw_provider": "lmstudio",
            "raw_model": str(body.get("model") or self.model),
        }

    def generate_weekly_report(self, *, report_context: dict) -> dict:
        payload = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 350,
            "response_format": self._weekly_report_response_format(),
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self._weekly_report_prompt(report_context)},
                    ],
                }
            ],
        }

        body = self._post_json(payload)
        content = self._extract_message_content(body)
        parsed = self._parse_weekly_report_payload(content)
        return {
            "highlights": parsed.highlights,
            "savings_insight": parsed.savings_insight,
            "conversation_starter": parsed.conversation_starter,
            "raw_provider": "lmstudio",
            "raw_model": str(body.get("model") or self.model),
        }

    def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
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
            return response.json()
        except requests.HTTPError as exc:
            response = getattr(exc, "response", None)
            status_code = getattr(response, "status_code", "unknown")
            response_text = ""
            if response is not None:
                try:
                    response_text = response.text.strip()
                except Exception:
                    response_text = ""
            detail = f"status={status_code}"
            if response_text:
                detail = f"{detail} body={response_text[:500]}"
            raise RuntimeError(f"LM Studio request failed. {detail}") from exc
        except Exception as exc:
            raise RuntimeError("LM Studio request failed.") from exc

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
        json_text = extract_json_text(content)
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("LM Studio returned invalid JSON.") from exc

        try:
            return _LMStudioVerificationPayload.model_validate(payload)
        except ValidationError as exc:
            raise RuntimeError("LM Studio response is missing required verification fields.") from exc

    def _parse_snap_payload(self, content: str) -> _LMStudioSnapAndLearnPayload:
        json_text = extract_json_text(content)
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("LM Studio returned invalid JSON.") from exc

        try:
            return _LMStudioSnapAndLearnPayload.model_validate(payload)
        except ValidationError as exc:
            raise RuntimeError("LM Studio response is missing required Snap & Learn fields.") from exc

    def _parse_weekly_report_payload(self, content: str) -> _LMStudioWeeklyReportPayload:
        json_text = extract_json_text(content)
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("LM Studio returned invalid JSON.") from exc

        try:
            return _LMStudioWeeklyReportPayload.model_validate(payload)
        except ValidationError as exc:
            raise RuntimeError("LM Studio response is missing required weekly report fields.") from exc

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

    def _inline_image_block(self, image_base64: str) -> dict[str, Any]:
        return {
            "type": "image_url",
            "image_url": {
                "url": image_base64,
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

    def _snap_response_format(self) -> dict[str, Any]:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "snap_and_learn_result",
                "schema": {
                    "type": "object",
                    "properties": {
                        "item_name": {"type": "string"},
                        "estimated_price": {"type": "string"},
                        "currency": {"type": "string"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "reasoning_summary": {"type": "string"},
                    },
                    "required": [
                        "item_name",
                        "estimated_price",
                        "currency",
                        "confidence",
                        "reasoning_summary",
                    ],
                    "additionalProperties": False,
                },
            },
        }

    def _weekly_report_response_format(self) -> dict[str, Any]:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "weekly_bloom_report",
                "schema": {
                    "type": "object",
                    "properties": {
                        "highlights": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "detail": {"type": "string"},
                                },
                                "required": ["title", "detail"],
                                "additionalProperties": False,
                            },
                        },
                        "savings_insight": {"type": "string"},
                        "conversation_starter": {"type": "string"},
                    },
                    "required": ["highlights", "savings_insight", "conversation_starter"],
                    "additionalProperties": False,
                },
            },
        }

    def _prompt(self, gig: dict) -> str:
        return build_verification_prompt(gig)

    def _snap_prompt(self) -> str:
        return build_snap_and_learn_prompt()

    def _weekly_report_prompt(self, report_context: dict) -> str:
        return build_weekly_report_prompt(report_context)
