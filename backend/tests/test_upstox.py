from datetime import datetime, timezone

import httpx
import pytest

from app.market.models import Timeframe
from app.market.upstox import UpstoxMarketDataFeed, UpstoxConfigurationError


@pytest.mark.asyncio
async def test_upstox_historical_candles_normalize():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/historical-candle/NSE_EQ%7CTEST/minutes/5/2026-09-01/2026-09-01" in str(request.url)
        assert request.headers["Authorization"] == "Bearer token"
        return httpx.Response(
            200,
            json={"status": "success", "data": {"candles": [[
                "2026-09-01T09:15:00+05:30", 25000, 25050, 24980, 25030, 100, 0
            ]]}}
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    feed = UpstoxMarketDataFeed("token", client)
    candles = await feed.fetch_candles(
        instrument_id="NSE_EQ|TEST",
        timeframe=Timeframe.M5,
        start_time=datetime(2026, 9, 1, tzinfo=timezone.utc),
        end_time=datetime(2026, 9, 1, 23, 59, tzinfo=timezone.utc),
    )
    await client.aclose()
    assert len(candles) == 1
    assert candles[0].close == 25030


def test_upstox_requires_token():
    with pytest.raises(UpstoxConfigurationError):
        UpstoxMarketDataFeed("")
