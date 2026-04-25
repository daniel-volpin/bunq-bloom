from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the API.

    LM Studio is the default local AI provider. Anthropic is the hosted
    production provider.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ai_provider: Literal["anthropic", "lmstudio"] = Field(default="lmstudio", alias="BLOOM_AI_PROVIDER")
    lmstudio_base_url: str = Field(default="http://127.0.0.1:1234/v1", alias="BLOOM_LMSTUDIO_BASE_URL")
    lmstudio_model: str | None = Field(default=None, alias="BLOOM_LMSTUDIO_MODEL")
    lmstudio_api_key: str | None = Field(default=None, alias="BLOOM_LMSTUDIO_API_KEY")
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

    def ai_mode(self) -> str:
        return "real"

    def ai_missing_config_codes(self) -> list[str]:
        if self.ai_provider == "anthropic":
            return [] if self.anthropic_api_key else ["anthropic_api_key_missing"]

        missing = []
        if not self.lmstudio_base_url:
            missing.append("lmstudio_base_url_missing")
        if not self.lmstudio_model:
            missing.append("lmstudio_model_missing")
        return missing

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
        if not (self.resolved_bunq_toolkit_path() / "bunq_client.py").exists():
            missing.append("bunq_toolkit_client_missing")
        return missing

    def resolved_bunq_toolkit_path(self) -> Path:
        path = self.bunq_toolkit_path
        if path.is_absolute():
            return path.resolve()

        cwd_candidate = (Path.cwd() / path).resolve()
        if (cwd_candidate / "bunq_client.py").exists():
            return cwd_candidate

        api_root_candidate = (Path(__file__).resolve().parents[1] / path).resolve()
        return api_root_candidate

    def resolved_bunq_toolkit_client_path(self) -> Path:
        return self.resolved_bunq_toolkit_path() / "bunq_client.py"


@lru_cache
def get_settings() -> Settings:
    return Settings()
