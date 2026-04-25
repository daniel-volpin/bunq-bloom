from app.models.domain import new_id
from app.models.verification import VerificationResultModel


class FakeVerificationClient:
    mode = "fake"

    def verify(self, *, gig: dict, before_photo: dict, after_photo: dict) -> dict:
        checklist = gig.get("verification_checklist") or ["task improved"]
        tags = [str(item) for item in checklist[:4]]
        return VerificationResultModel(
            id=new_id("verif"),
            gig_id=gig["id"],
            approved=True,
            confidence=0.92,
            tags=tags,
            message_for_kid=self._message(tags),
            reasoning_summary="Fake verification approved this task for the local core-loop demo.",
            raw_provider="fake",
            raw_model="fake-verification-v1",
        ).model_dump()

    def analyze(self, *, image_base64: str) -> dict:
        return {
            "item_name": "Nintendo Switch Game",
            "estimated_price": {"amount": "24.99", "currency": "EUR"},
            "confidence": 0.91,
            "reasoning_summary": "Fake analysis recognized a game case for the local demo.",
            "raw_provider": "fake",
            "raw_model": "fake-snap-v1",
        }

    def generate_weekly_report(self, *, report_context: dict) -> dict:
        stats = report_context.get("stats", {})
        gigs_completed = int(stats.get("gigs_completed", 0) or 0)
        earned = stats.get("money_earned", {}).get("amount", "0.00")
        average_reward = stats.get("average_reward", {}).get("amount", "0.00")
        highlights = report_context.get("highlights") or []
        top_highlight = highlights[0] if highlights else {"title": "Weekly reset", "detail": "No paid gigs were recorded this week yet."}

        if gigs_completed == 0:
            savings_insight = "No paid gigs landed this week yet. One completed gig can start the savings habit again."
            conversation_starter = "What is one small gig you want to finish first next week?"
        else:
            savings_insight = (
                f"EUR {earned} earned this week means steady progress, with an average of EUR {average_reward} per paid gig."
            )
            conversation_starter = "Which reward felt most worth the effort this week?"

        return {
            "highlights": [
                {
                    "title": top_highlight.get("title", "Family win"),
                    "detail": top_highlight.get("detail", "A completed gig moved savings forward this week."),
                },
                {
                    "title": "Weekly momentum",
                    "detail": f"{gigs_completed} paid gigs brought in EUR {earned} this week.",
                },
            ] if gigs_completed > 0 else [top_highlight],
            "savings_insight": savings_insight,
            "conversation_starter": conversation_starter,
            "raw_provider": "fake",
            "raw_model": "fake-bloom-v1",
        }

    def _message(self, tags: list[str]) -> str:
        if tags:
            return f"Nice work. I can see: {', '.join(tags)}."
        return "Nice work. This looks ready."
