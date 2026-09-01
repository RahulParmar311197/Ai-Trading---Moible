from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.market.feed import MarketDataFeed
from app.market.models import Candle, MarketEvent, Timeframe
from app.market.provider_runtime import ProviderMarketRunner


class FakeFeed(MarketDataFeed):
    provider = "test"

    async def fetch_candles(self, *, instrument_id, timeframe, start_time, end_time):
        return []

    async def stream(self, *, instrument_ids):
        yield MarketEvent(
            instrument_id=instrument_ids[0],
            timestamp=datetime(2026, 9, 1, 9, 15, tzinfo=timezone.utc),
            timeframe=Timeframe.M15,
            open=Decimal("25000"), high=Decimal("25050"),
            low=Decimal("24980"), close=Decimal("25030"), volume=Decimal("100"),
        )


@pytest.mark.asyncio
async def test_provider_runner_forwards_normalized_events():
    received = []
    runner = ProviderMarketRunner(FakeFeed(), received.append)
    # publish is async in production; keep the test explicit about that boundary.
    async def publish(event):
        received.append(event)
    runner.publish = publish

    await runner.run(["nifty-front"])
    assert len(received) == 1
    assert received[0].instrument_id == "nifty-front"
