from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str
    message: str
    retryable: bool = False


class ErrorResponse(BaseModel):
    error: ErrorBody


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

