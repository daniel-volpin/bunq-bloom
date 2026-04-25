from typing import Literal

from pydantic import BaseModel, Field

Currency = Literal["EUR"]
GigStatus = Literal[
    "open",
    "claimed",
    "awaiting_after_photo",
    "verifying",
    "approved",
    "paid",
    "rejected",
    "payment_failed",
]
CompletionMode = Literal["fake_local", "fake_ai", "real", "ai_fallback", "bunq_fallback"]
AiMode = Literal["real", "fake", "fallback"]
PaymentMode = Literal["real", "fake_local", "bunq_fallback"]
BalanceRefreshStatus = Literal["pending", "ok", "failed"]
PaymentStatus = Literal["succeeded", "failed"]


class ErrorBody(BaseModel):
    code: str
    message: str
    retryable: bool = False


class ErrorResponse(BaseModel):
    error: ErrorBody


class IntegrationStatus(BaseModel):
    mode: str
    ready: bool
    status: str
    missing_config: list[str] = Field(default_factory=list)


class PathStatus(BaseModel):
    ready: bool
    status: str
    exists: bool | None = None
    readable: bool | None = None
    writable: bool | None = None
    creatable: bool | None = None
    missing_config: list[str] = Field(default_factory=list)


class StateStatus(BaseModel):
    ready: bool
    status: str
    path_parent: PathStatus
    missing_config: list[str] = Field(default_factory=list)


class HealthIntegrations(BaseModel):
    ai: IntegrationStatus
    bunq: IntegrationStatus
    state: StateStatus
    uploads: PathStatus


class HealthResponse(BaseModel):
    status: str
    readiness_status: str
    integrations: HealthIntegrations


class MoneyAmount(BaseModel):
    amount: str
    currency: Currency


class BalanceSnapshot(BaseModel):
    amount: str
    currency: Currency
    source: str


class SnapAndLearnRequest(BaseModel):
    image_base64: str


class SnapAndLearnAnalysis(BaseModel):
    item_name: str
    estimated_price: MoneyAmount
    gigs_needed: int
    suggested_goal: str
    confidence: float | None = None


class SnapAndLearnResponse(BaseModel):
    analysis: SnapAndLearnAnalysis
    kid_balance: BalanceSnapshot
    mode: CompletionMode
    ai_mode: AiMode
    payment_mode: PaymentMode
    fallback_mode: bool


class BloomReportPeriod(BaseModel):
    start_date: str
    end_date: str


class BloomReportStats(BaseModel):
    gigs_completed: int
    money_earned: MoneyAmount
    average_reward: MoneyAmount
    current_balance: BalanceSnapshot


class BloomReportHighlight(BaseModel):
    title: str
    detail: str


class BloomReportResponse(BaseModel):
    period: BloomReportPeriod
    stats: BloomReportStats
    highlights: list[BloomReportHighlight]
    savings_insight: str
    conversation_starter: str
    mode: CompletionMode
    fallback_mode: bool


class GigResponse(BaseModel):
    id: str
    family_id: str
    title: str
    description: str
    reward_amount: str
    currency: Currency
    status: GigStatus
    created_by_user_id: str
    claimed_by_user_id: str | None = None
    verification_checklist: list[str] = Field(default_factory=list)
    before_photo_id: str | None = None
    after_photo_id: str | None = None
    verification_result_id: str | None = None
    payment_id: str | None = None
    created_at: str
    updated_at: str


class GigEnvelopeResponse(BaseModel):
    gig: GigResponse


class ListGigsResponse(BaseModel):
    gigs: list[GigResponse]


class VerificationResponse(BaseModel):
    approved: bool
    confidence: float
    tags: list[str]
    message_for_kid: str


class PaymentResponse(BaseModel):
    status: PaymentStatus
    amount: str
    currency: Currency
    bunq_payment_id: str | None = None
    merchant_reference: str | None = None
    error_code: str | None = None
    retryable: bool | None = None


class CompleteGigResponse(BaseModel):
    gig: GigResponse
    verification: VerificationResponse
    payment: PaymentResponse | None = None
    kid_balance: BalanceSnapshot | None = None
    mode: CompletionMode
    ai_mode: AiMode
    payment_mode: PaymentMode
    fallback_mode: bool
    balance_refresh_status: BalanceRefreshStatus | None = None
    balance_refresh_error: str | None = None


class BalanceResponse(BaseModel):
    balance: BalanceSnapshot
    mode: PaymentMode
    fallback_mode: bool


class GigCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    reward_amount: str
    currency: str = "EUR"
    verification_checklist: list[str] = Field(default_factory=list)


class BeforePhotoRequest(BaseModel):
    image_base64: str


class CompleteGigRequest(BaseModel):
    after_image_base64: str
    idempotency_key: str = Field(min_length=8, max_length=120)


class RetryPaymentRequest(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=120)
