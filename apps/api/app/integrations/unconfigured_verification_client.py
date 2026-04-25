from app.errors import AppError


class UnconfiguredVerificationClient:
    def __init__(self, *, provider: str):
        self.provider = provider
        self.mode = "real"

    def verify(self, *, gig: dict, before_photo: dict, after_photo: dict) -> dict:
        raise AppError(
            "verification_not_configured",
            f"AI provider '{self.provider}' is not configured.",
            status_code=500,
            retryable=False,
        )

    def analyze(self, *, image_base64: str) -> dict:
        raise AppError(
            "analysis_not_configured",
            f"AI provider '{self.provider}' is not configured.",
            status_code=500,
            retryable=False,
        )

    def generate_weekly_report(self, *, report_context: dict) -> dict:
        raise AppError(
            "report_generation_not_configured",
            f"AI provider '{self.provider}' is not configured.",
            status_code=500,
            retryable=False,
        )