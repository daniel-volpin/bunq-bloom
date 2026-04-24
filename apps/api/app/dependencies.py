from functools import lru_cache

from app.integrations.bunq_payment_client import BunqPaymentClient
from app.integrations.fake_payment_client import FakePaymentClient
from app.integrations.fake_verification_client import FakeVerificationClient
from app.repositories.photo_repository import PhotoRepository
from app.repositories.state_repository import StateRepository
from app.services.gig_service import GigService
from app.services.payment_service import PaymentService
from app.settings import get_settings


@lru_cache
def get_gig_service() -> GigService:
    settings = get_settings()
    state_repository = StateRepository(settings.state_path)
    photo_repository = PhotoRepository(settings.upload_dir)
    verification_client = FakeVerificationClient()
    payment_client = FakePaymentClient() if settings.use_fake_bunq else BunqPaymentClient(settings)
    payment_service = PaymentService(payment_client)
    return GigService(
        state_repository=state_repository,
        photo_repository=photo_repository,
        verification_client=verification_client,
        payment_service=payment_service,
        allow_ai_fallback=settings.demo_allow_ai_fallback,
    )
