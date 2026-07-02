from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE_PATH = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    DATABASE_URL: str = Field(
        "sqlite:///linkedin_ai.db",
        validation_alias="DATABASE_URL",
    )
    OPENAI_API_KEY: str = Field("", validation_alias="OPENAI_API_KEY")
    OPENAI_BASE_URL: str = Field(
        "https://api.openai.com/v1",
        validation_alias="OPENAI_BASE_URL",
    )
    GPT_MODEL: str = Field("gpt-5.5", validation_alias="GPT_MODEL")
    GPT_TEMPERATURE: float = Field(0.7, validation_alias="GPT_TEMPERATURE")
    GPT_MAX_TOKENS: int = Field(600, validation_alias="GPT_MAX_TOKENS")
    POST_TIME: str = Field("08:00", validation_alias="POST_TIME")
    TIMEZONE: str = Field("UTC", validation_alias="TIMEZONE")
    host: str = Field("127.0.0.1", validation_alias="HOST")
    port: int = Field(8000, validation_alias="PORT")
    LINKEDIN_CLIENT_ID: str = Field("", validation_alias="LINKEDIN_CLIENT_ID")
    LINKEDIN_CLIENT_SECRET: str = Field("", validation_alias="LINKEDIN_CLIENT_SECRET")
    LINKEDIN_REDIRECT_URI: str = Field("", validation_alias="LINKEDIN_REDIRECT_URI")
    LINKEDIN_SCOPES: str = Field("", validation_alias="LINKEDIN_SCOPES")
    LINKEDIN_TOKEN_SECRET: str = Field("", validation_alias="LINKEDIN_TOKEN_SECRET")
    LINKEDIN_OAUTH_STATE_TTL_SECONDS: int = Field(
        600,
        validation_alias="LINKEDIN_OAUTH_STATE_TTL_SECONDS",
    )
    PUBLISH_RETRY_DELAY_SECONDS: int = Field(
        300,
        validation_alias="PUBLISH_RETRY_DELAY_SECONDS",
    )

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        extra="ignore",
    )


settings = Settings()
