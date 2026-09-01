"""Concrete provider selection boundary.

A real provider must be explicitly configured. We never fabricate credentials
or silently fall back to simulated market data.
"""

from app.config import settings
from app.market.feed import MarketDataFeed


class ProviderConfigurationError(RuntimeError):
    pass


def get_market_data_feed() -> MarketDataFeed:
    provider = settings.market_data_provider.strip().lower()
    if not provider:
        raise ProviderConfigurationError(
            "MARKET_DATA_PROVIDER is not configured; refusing to start live market data"
        )
    raise ProviderConfigurationError(
        f"No concrete market-data adapter is installed for provider '{provider}'"
    )
