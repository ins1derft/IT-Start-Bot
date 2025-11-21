from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    bot_token: str = "change-me"
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = Field(
        "postgresql+asyncpg://itstart:itstart@localhost:5432/itstart", validation_alias="POSTGRES_DSN"
    )
    sentry_dsn: str | None = None
    bot_channel_id: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
