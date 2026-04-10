"""Application settings loaded from environment variables."""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for API, workers, and infrastructure clients."""

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
        description="PostgreSQL DSN",
    )
    redis_url: str = Field(default="redis://localhost:6379/0")

    telegram_bot_token: str = Field(default="")
    webhook_url: str = Field(default="")
    telegram_secret_token: str = Field(default="")

    openai_api_key: str = Field(default="")

    app_env: str = Field(default="development")
    secret_key: str = Field(default="dev-secret-key")
    debug: bool = Field(default=True)

    session_idle_threshold_minutes: int = Field(default=60)
    llm_confidence_threshold: float = Field(default=0.7)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: object) -> bool:
        """Allow broader DEBUG env values such as 'release'."""
        if isinstance(value, bool):
            return value
        if value is None:
            return True

        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "on", "debug", "development"}:
            return True
        if normalized in {"0", "false", "no", "off", "release", "prod", "production"}:
            return False
        return True


settings = Settings()
