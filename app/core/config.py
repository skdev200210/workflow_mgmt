from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment / .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Agent Service"

    # Root log level for the JSON logs (DEBUG/INFO/WARNING/...).
    log_level: str = "INFO"
    # Echo every SQL statement (very noisy) — opt-in for debugging only.
    sql_echo: bool = False

    # API key required in the X-API-Key header for /agents routes.
    api_key: str = "changeme-dev-key"

    # Allowed CORS origins for the browser frontend. Comma-separated in env
    cors_origins: list[str] = ["*"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, v: object) -> object:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    # Worker: how many due queue rows to claim per poll, and how long to sleep
    # when a poll finds nothing
    worker_batch_size: int = 100
    worker_poll_interval: float = 10.0

    # Fire-and-forget dispatch: how long to wait for the external service's
    # callback before the sweeper reclaims an in_flight row.
    dispatch_timeout_seconds: int = 3600
    # Fallback retry delay when neither the callback payload nor the workflow's
    # calling_config specifies one.
    default_retry_seconds: int = 1800
    # Dispatch attempts allowed per node before a row is dead-lettered.
    default_max_attempts: int = 3

    database_url: str


@lru_cache
def get_settings() -> Settings:
    return Settings()
