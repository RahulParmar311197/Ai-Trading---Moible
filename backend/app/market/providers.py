"""Concrete provider selection boundary.

A real provider must be explicitly configured. We never fabricate credentials
or silently fall back to simulated market data.
"""

from app.config import settings
from app.market.feed import MarketDataFeed
from app.market.upstox import UpstoxMarketDataFeed


class ProviderConfigurationError(RuntimeError):
    pass


def get_market_data_feed() -> MarketDataFeed:
    provider = settings.market_data_provider.strip().lower()
    if not provider:
        raise ProviderConfigurationError(
            "MARKET_DATA_PROVIDER is not configured; refusing to start live market data"
        )
    if provider == "upstox":
        if not settings.upstox_access_token:
            raise ProviderConfigurationError("UPSTOX_ACCESS_TOKEN is required for Upstox")
        return UpstoxMarketDataFeed(settings.upstox_access_token)
    raise ProviderConfigurationError(
        f"No concrete market-data adapter is installed for provider '{provider}'"
    )
