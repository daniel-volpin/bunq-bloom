from pydantic import BaseModel, Field


class VerificationResultModel(BaseModel):
    id: str
    gig_id: str
    approved: bool
    confidence: float = Field(ge=0, le=1)
    tags: list[str]
    message_for_kid: str = Field(min_length=1, max_length=300)
    reasoning_summary: str = Field(min_length=1, max_length=1000)
    raw_provider: str
    raw_model: str

