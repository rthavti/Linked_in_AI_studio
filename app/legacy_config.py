from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):

    app_name: str = "LinkedIn AI Studio"

    host: str = "127.0.0.1"

    port: int = 8000

    log_level: str = "INFO"

    database_url: str = "sqlite:///linkedin_ai.db"

    openai_api_key: str = ""

    openai_base_url: str = "https://api.openai.com/v1"

    openai_model: str = "gpt-4.1"

    image_provider: str = "openai"

    linkedin_email: str = ""

    linkedin_password: str = ""

    post_time: str = "10:00"

    timezone: str = "Asia/Kolkata"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()