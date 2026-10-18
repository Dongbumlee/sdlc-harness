from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuration(BaseSettings):
    """Application configuration, populated from environment / .env."""

    model_config = SettingsConfigDict(extra="ignore")

    app_name: str = "{{ProjectName}} API"
    app_env: str = "local"
