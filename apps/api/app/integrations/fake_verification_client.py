from app.models.domain import new_id


class FakeVerificationClient:
    def verify(self, *, gig: dict, before_photo: dict, after_photo: dict) -> dict:
        checklist = gig.get("verification_checklist") or ["task improved"]
        tags = [str(item) for item in checklist[:4]]
        return {
            "id": new_id("verif"),
            "gig_id": gig["id"],
            "approved": True,
            "confidence": 0.92,
            "tags": tags,
            "message_for_kid": self._message(tags),
            "reasoning_summary": "Fake verification approved this task for the local core-loop demo.",
            "raw_provider": "fake",
            "raw_model": "fake-verification-v1",
        }

    def _message(self, tags: list[str]) -> str:
        if tags:
            return f"Nice work. I can see: {', '.join(tags)}."
        return "Nice work. This looks ready."

