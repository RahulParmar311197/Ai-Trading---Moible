"""Application configuration loaded from environment variables."""

from decimal import Decimal

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
    upstox_sandbox_access_token: str = ""

    # Controlled execution remains inert unless all required execution settings
    # are explicitly supplied. These settings never activate trading by themselves.
    execution_broker: str = ""
    execution_sandbox: bool = False
    execution_allow_live_orders: bool = False
    execution_allow_sandbox_orders: bool = False
    execution_confirmation_phrase: str = ""
    trading_session_id: str = ""
    execution_max_order_notional: Decimal | None = None
    execution_max_position_quantity: int | None = None
    execution_max_daily_loss: Decimal | None = None

    ai_provider_url: str = ""
    ai_provider_api_key: str = ""
    ai_provider_model: str = ""
    ai_provider_timeout_seconds: float = 20.0

    @property
    def configured_market_data_instruments(self) -> list[str]:
        return [item.strip() for item in self.market_data_instrument_ids.split(",") if item.strip()]


settings = Settings()
