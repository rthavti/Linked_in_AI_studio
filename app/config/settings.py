from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = Field(
        "sqlite:///linkedin_ai.db",
        env="DATABASE_URL",
    )
    OPENAI_API_KEY: str = Field("", env="OPENAI_API_KEY")
    OPENAI_BASE_URL: str = Field(
        "https://api.openai.com/v1",
        env="OPENAI_BASE_URL",
    )
    GPT_MODEL: str = Field("gpt-5.5", env="GPT_MODEL")
    GPT_TEMPERATURE: float = Field(0.7, env="GPT_TEMPERATURE")
    GPT_MAX_TOKENS: int = Field(600, env="GPT_MAX_TOKENS")
    POST_TIME: str = Field("08:00", env="POST_TIME")
    TIMEZONE: str = Field("UTC", env="TIMEZONE")
    host: str = Field("127.0.0.1", env="HOST")
    port: int = Field(8000, env="PORT")
    LINKEDIN_CLIENT_ID: str = Field("", env="LINKEDIN_CLIENT_ID")
    LINKEDIN_CLIENT_SECRET: str = Field("", env="LINKEDIN_CLIENT_SECRET")
    LINKEDIN_REDIRECT_URI: str = Field("", env="LINKEDIN_REDIRECT_URI")
    LINKEDIN_SCOPES: str = Field("", env="LINKEDIN_SCOPES")
    LINKEDIN_TOKEN_SECRET: str = Field("", env="LINKEDIN_TOKEN_SECRET")
    LINKEDIN_OAUTH_STATE_TTL_SECONDS: int = Field(
        600,
        env="LINKEDIN_OAUTH_STATE_TTL_SECONDS",
    )
    PUBLISH_RETRY_DELAY_SECONDS: int = Field(
        300,
        env="PUBLISH_RETRY_DELAY_SECONDS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
