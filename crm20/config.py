from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Real Estate CRM Agent"
    environment: str = "development"

    database_url: str = "sqlite:///./poc20.db"

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    timezone: str = "Asia/Kolkata"

    calendar_credentials_path: str = "credentials.json"
    calendar_token_path: str = "token.json"

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()