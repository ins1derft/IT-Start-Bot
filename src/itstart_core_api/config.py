from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = Field(
        "postgresql+asyncpg://itstart:itstart@localhost:5432/itstart", validation_alias="POSTGRES_DSN"
    )
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me"
    access_token_ttl_sec: int = 3600
    refresh_token_ttl_sec: int = 60 * 60 * 24 * 14
    sentry_dsn: Optional[str] = None
    prometheus_port: int = 9090


@lru_cache
def get_settings() -> Settings:
    return Settings()
