from functools import lru_cache

from app.integrations.bunq_payment_client import BunqPaymentClient
from app.integrations.claude_client import ClaudeVisionClient
from app.integrations.fake_payment_client import FakePaymentClient
from app.integrations.lmstudio_client import LMStudioVisionClient
from app.integrations.unconfigured_verification_client import UnconfiguredVerificationClient
from app.repositories.photo_repository import PhotoRepository
from app.repositories.state_repository import StateRepository
from app.services.bloom_report_service import BloomReportService
from app.services.gig_service import GigService
from app.services.payment_service import PaymentService
from app.services.snap_and_learn_service import SnapAndLearnService
from app.settings import get_settings


def _build_ai_client(settings):
    if settings.ai_provider == "lmstudio":
        if settings.lmstudio_model and settings.lmstudio_base_url:
            return LMStudioVisionClient(
                base_url=settings.lmstudio_base_url,
                model=settings.lmstudio_model,
                api_key=settings.lmstudio_api_key,
            )
        return UnconfiguredVerificationClient(provider="lmstudio")

    return (
        ClaudeVisionClient(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
        )
        if settings.anthropic_api_key
        else UnconfiguredVerificationClient(provider="anthropic")
    )


def _build_state_repository(settings) -> StateRepository:
    return StateRepository(settings.state_path)


def _build_photo_repository(settings) -> PhotoRepository:
    return PhotoRepository(settings.upload_dir)


def _build_payment_client(settings):
    return FakePaymentClient() if settings.use_fake_bunq else BunqPaymentClient(settings)


def _build_payment_service(settings) -> PaymentService:
    return PaymentService(_build_payment_client(settings))


@lru_cache
def get_gig_service() -> GigService:
    settings = get_settings()
    return GigService(
        state_repository=_build_state_repository(settings),
        photo_repository=_build_photo_repository(settings),
        verification_client=_build_ai_client(settings),
        payment_service=_build_payment_service(settings),
        allow_ai_fallback=settings.demo_allow_ai_fallback,
    )


@lru_cache
def get_snap_and_learn_service() -> SnapAndLearnService:
    settings = get_settings()
    return SnapAndLearnService(
        state_repository=_build_state_repository(settings),
        photo_repository=_build_photo_repository(settings),
        analysis_client=_build_ai_client(settings),
        payment_service=_build_payment_service(settings),
        allow_ai_fallback=settings.demo_allow_ai_fallback,
    )


@lru_cache
def get_bloom_report_service() -> BloomReportService:
    settings = get_settings()
    return BloomReportService(
        state_repository=_build_state_repository(settings),
        narrative_client=_build_ai_client(settings),
        allow_ai_fallback=settings.demo_allow_ai_fallback,
    )
