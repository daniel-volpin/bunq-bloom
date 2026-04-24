from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the API.

    Fake adapters are the default so the M1 core loop runs without external
    credentials.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    use_fake_ai: bool = Field(default=True, alias="BLOOM_USE_FAKE_AI")
    use_fake_bunq: bool = Field(default=True, alias="BLOOM_USE_FAKE_BUNQ")
    demo_allow_ai_fallback: bool = Field(default=False, alias="BLOOM_DEMO_ALLOW_AI_FALLBACK")
    demo_allow_bunq_fallback: bool = Field(default=False, alias="BLOOM_DEMO_ALLOW_BUNQ_FALLBACK")
    state_path: Path = Field(default=Path("data/state.json"), alias="BLOOM_STATE_PATH")
    upload_dir: Path = Field(default=Path("data/uploads"), alias="BLOOM_UPLOAD_DIR")
    bunq_toolkit_path: Path = Field(default=Path("../../hackathon_toolkit-main"), alias="BLOOM_BUNQ_TOOLKIT_PATH")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    bunq_api_key: str | None = Field(default=None, alias="BUNQ_API_KEY")
    bunq_parent_account_id: str | None = Field(default=None, alias="BUNQ_PARENT_ACCOUNT_ID")
    bunq_kid_account_id: str | None = Field(default=None, alias="BUNQ_KID_ACCOUNT_ID")


@lru_cache
def get_settings() -> Settings:
    return Settings()
