import base64
from pathlib import Path

from app.errors import AppError
from app.models.domain import new_id


MAX_IMAGE_BYTES = 8 * 1024 * 1024
SUPPORTED_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


class PhotoRepository:
    def __init__(self, upload_dir: Path):
        self.upload_dir = upload_dir

    def save_data_url(self, image_base64: str, *, gig_id: str, kind: str) -> dict[str, str]:
        content_type, raw = self.validate_data_url(image_base64)

        photo_id = new_id("photo")
        extension = SUPPORTED_TYPES[content_type]
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        storage_ref = self.upload_dir / f"{photo_id}.{extension}"
        storage_ref.write_bytes(raw)
        return {
            "id": photo_id,
            "gig_id": gig_id,
            "kind": kind,
            "content_type": content_type,
            "storage_ref": str(storage_ref),
        }

    def validate_data_url(self, image_base64: str) -> tuple[str, bytes]:
        content_type, payload = self._parse_data_url(image_base64)
        raw = self._decode(payload)
        if len(raw) > MAX_IMAGE_BYTES:
            raise AppError("image_too_large", "Image must be 8 MB or smaller.", status_code=413)
        return content_type, raw

    def _parse_data_url(self, value: str) -> tuple[str, str]:
        if not value.startswith("data:") or ";base64," not in value:
            raise AppError("invalid_image_type", "Image must be a base64 data URL.")
        header, payload = value.split(";base64,", 1)
        content_type = header.removeprefix("data:")
        if content_type not in SUPPORTED_TYPES:
            raise AppError("invalid_image_type", "Supported image types are JPEG, PNG, and WebP.")
        return content_type, payload

    def _decode(self, payload: str) -> bytes:
        try:
            return base64.b64decode(payload, validate=True)
        except ValueError as exc:
            raise AppError("invalid_image_type", "Image payload is not valid base64.") from exc

