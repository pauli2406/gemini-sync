from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/gemini_sync_bridge",
        alias="DATABASE_URL",
    )
    google_cloud_project: str = Field(default="", alias="GOOGLE_CLOUD_PROJECT")
    gemini_ingestion_dry_run: bool = Field(default=True, alias="GEMINI_INGESTION_DRY_RUN")
    teams_webhook_url: str = Field(default="", alias="TEAMS_WEBHOOK_URL")
    splunk_hec_url: str = Field(default="", alias="SPLUNK_HEC_URL")
    splunk_hec_token: str = Field(default="", alias="SPLUNK_HEC_TOKEN")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    max_retries: int = Field(default=3, alias="MAX_RETRIES")
    retry_backoff_seconds: float = Field(default=2.0, alias="RETRY_BACKOFF_SECONDS")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
