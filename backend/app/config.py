"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/ai_trading"
    redis_url: str = "redis://localhost:6379/0"
    market_data_provider: str = ""
    market_data_instrument_ids: str = ""
    upstox_access_token: str = ""
    ai_provider_url: str = ""
    ai_provider_api_key: str = ""
    ai_provider_model: str = ""
    ai_provider_timeout_seconds: float = 20.0

    @property
    def configured_market_data_instruments(self) -> list[str]:
        return [item.strip() for item in self.market_data_instrument_ids.split(",") if item.strip()]


settings = Settings()
