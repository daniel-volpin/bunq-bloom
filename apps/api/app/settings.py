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

    def claude_mode(self) -> str:
        return "fake" if self.use_fake_ai else "real"

    def claude_missing_config_codes(self) -> list[str]:
        if self.use_fake_ai:
            return []
        return [] if self.anthropic_api_key else ["anthropic_api_key_missing"]

    def bunq_mode(self) -> str:
        return "fake" if self.use_fake_bunq else "real"

    def bunq_missing_config_codes(self) -> list[str]:
        if self.use_fake_bunq:
            return []

        missing = []
        if not self.bunq_api_key:
            missing.append("bunq_api_key_missing")
        if not self.bunq_parent_account_id:
            missing.append("bunq_parent_account_id_missing")
        if not self.bunq_kid_account_id:
            missing.append("bunq_kid_account_id_missing")
        if not self.resolved_bunq_toolkit_client_path().exists():
            missing.append("bunq_toolkit_client_missing")
        return missing

    def resolved_bunq_toolkit_client_path(self) -> Path:
        path = self.bunq_toolkit_path
        if not path.is_absolute():
            path = Path.cwd() / path
        return path.resolve() / "bunq_client.py"


@lru_cache
def get_settings() -> Settings:
    return Settings()
