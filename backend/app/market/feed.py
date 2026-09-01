"""Provider-neutral market-data adapter contract.

The blueprint places the adapter between provider transport (REST/WebSocket)
and normalization. Concrete broker/data-provider clients implement this
contract; provider payloads must not leak into downstream strategy code.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import datetime

from .models import Candle, MarketEvent, Timeframe


class MarketDataFeed(ABC):
    """Common interface for historical and streaming market data."""

    provider: str

    @abstractmethod
    async def fetch_candles(
        self,
        *,
        instrument_id: str,
        timeframe: Timeframe,
        start_time: datetime,
        end_time: datetime,
    ) -> list[Candle]:
        """Fetch historical candles in canonical form."""
        raise NotImplementedError

    @abstractmethod
    async def stream(self, *, instrument_ids: list[str]) -> AsyncIterator[MarketEvent]:
        """Yield normalized market events from the provider stream."""
        raise NotImplementedError
