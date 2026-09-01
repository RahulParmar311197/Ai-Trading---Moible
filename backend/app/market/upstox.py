"""Upstox V3 historical market-data adapter.

The V3 historical-candle API is JSON and maps cleanly into the canonical
Candle model. The real-time V3 feed remains a separate transport because it
uses an authorized WebSocket and Protobuf payloads.
"""

from collections.abc import AsyncIterator
from datetime import datetime
from decimal import Decimal
from urllib.parse import quote

import httpx

from .feed import MarketDataFeed
from .models import Candle, MarketEvent, Timeframe


class UpstoxConfigurationError(RuntimeError):
    pass


class UpstoxMarketDataFeed(MarketDataFeed):
    provider = "upstox"
    BASE_URL = "https://api.upstox.com/v3"

    def __init__(self, access_token: str, client: httpx.AsyncClient | None = None) -> None:
        if not access_token.strip():
            raise UpstoxConfigurationError("UPSTOX_ACCESS_TOKEN is required")
        self.access_token = access_token
        self._client = client

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }

    @staticmethod
    def _unit_interval(timeframe: Timeframe) -> tuple[str, str]:
        mapping = {
            Timeframe.M1: ("minutes", "1"),
            Timeframe.M3: ("minutes", "3"),
            Timeframe.M5: ("minutes", "5"),
            Timeframe.M15: ("minutes", "15"),
            Timeframe.M30: ("minutes", "30"),
            Timeframe.H1: ("hours", "1"),
            Timeframe.H2: ("hours", "2"),
            Timeframe.H4: ("hours", "4"),
            Timeframe.D1: ("days", "1"),
            Timeframe.W1: ("weeks", "1"),
        }
        try:
            return mapping[timeframe]
        except KeyError as exc:
            raise ValueError(f"Unsupported Upstox timeframe: {timeframe}") from exc

    async def fetch_candles(
        self,
        *,
        instrument_id: str,
        timeframe: Timeframe,
        start_time: datetime,
        end_time: datetime,
    ) -> list[Candle]:
        unit, interval = self._unit_interval(timeframe)
        instrument_key = quote(instrument_id, safe="")
        url = (
            f"{self.BASE_URL}/historical-candle/{instrument_key}/"
            f"{unit}/{interval}/{end_time.date().isoformat()}/{start_time.date().isoformat()}"
        )
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=15.0)
        try:
            response = await client.get(url, headers=self._headers())
            response.raise_for_status()
            payload = response.json()
        finally:
            if owns_client:
                await client.aclose()

        candles: list[Candle] = []
        for row in payload.get("data", {}).get("candles", []):
            timestamp, open_, high, low, close, volume, *_ = row
            candle = Candle(
                instrument_id=instrument_id,
                timestamp=datetime.fromisoformat(timestamp),
                timeframe=timeframe,
                open=Decimal(str(open_)),
                high=Decimal(str(high)),
                low=Decimal(str(low)),
                close=Decimal(str(close)),
                volume=Decimal(str(volume)),
            )
            candles.append(candle.validate_ohlc())
        return candles

    async def stream(self, *, instrument_ids: list[str]) -> AsyncIterator[MarketEvent]:
        raise NotImplementedError(
            "Upstox V3 live feed requires the official Protobuf decoder and authorized WebSocket transport"
        )
