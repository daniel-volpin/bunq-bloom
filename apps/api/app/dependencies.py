from functools import lru_cache

from app.integrations.bunq_payment_client import BunqPaymentClient
from app.integrations.claude_client import ClaudeVisionClient
from app.integrations.fake_payment_client import FakePaymentClient
from app.integrations.fake_verification_client import FakeVerificationClient
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
        return FakeVerificationClient() if settings.use_fake_bunq else UnconfiguredVerificationClient(provider="lmstudio")

    return (
        ClaudeVisionClient(api_key=settings.anthropic_api_key)
        if settings.anthropic_api_key
        else FakeVerificationClient() if settings.use_fake_bunq else UnconfiguredVerificationClient(provider="anthropic")
    )


@lru_cache
def get_gig_service() -> GigService:
    settings = get_settings()
    state_repository = StateRepository(settings.state_path)
    photo_repository = PhotoRepository(settings.upload_dir)
    verification_client = _build_ai_client(settings)

    payment_client = FakePaymentClient() if settings.use_fake_bunq else BunqPaymentClient(settings)
    payment_service = PaymentService(payment_client)
    return GigService(
        state_repository=state_repository,
        photo_repository=photo_repository,
        verification_client=verification_client,
        payment_service=payment_service,
        allow_ai_fallback=settings.demo_allow_ai_fallback,
    )


@lru_cache
def get_snap_and_learn_service() -> SnapAndLearnService:
    settings = get_settings()
    state_repository = StateRepository(settings.state_path)
    photo_repository = PhotoRepository(settings.upload_dir)
    payment_client = FakePaymentClient() if settings.use_fake_bunq else BunqPaymentClient(settings)
    payment_service = PaymentService(payment_client)
    return SnapAndLearnService(
        state_repository=state_repository,
        photo_repository=photo_repository,
        analysis_client=_build_ai_client(settings),
        payment_service=payment_service,
        allow_ai_fallback=settings.demo_allow_ai_fallback,
    )


@lru_cache
def get_bloom_report_service() -> BloomReportService:
    settings = get_settings()
    state_repository = StateRepository(settings.state_path)
    return BloomReportService(
        state_repository=state_repository,
        narrative_client=_build_ai_client(settings),
        allow_ai_fallback=settings.demo_allow_ai_fallback,
    )
