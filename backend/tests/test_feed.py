from collections.abc import AsyncIterator
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.market.feed import MarketDataFeed
from app.market.models import Candle, MarketEvent, Timeframe


class FakeFeed(MarketDataFeed):
    provider = "test"

    async def fetch_candles(self, *, instrument_id, timeframe, start_time, end_time):
        return [
            Candle(
                instrument_id=instrument_id,
                timestamp=start_time,
                timeframe=timeframe,
                open=Decimal("100"),
                high=Decimal("105"),
                low=Decimal("95"),
                close=Decimal("102"),
            )
        ]

    async def stream(self, *, instrument_ids) -> AsyncIterator[MarketEvent]:
        for instrument_id in instrument_ids:
            yield MarketEvent(
                instrument_id=instrument_id,
                timestamp=datetime(2026, 9, 1, 9, 15, tzinfo=timezone.utc),
                timeframe=Timeframe.M1,
                open=Decimal("100"),
                high=Decimal("101"),
                low=Decimal("99"),
                close=Decimal("100.5"),
            )


@pytest.mark.asyncio
async def test_feed_contract_supports_history_and_stream() -> None:
    feed = FakeFeed()
    start = datetime(2026, 9, 1, 9, 15, tzinfo=timezone.utc)
    candles = await feed.fetch_candles(
        instrument_id="nifty-front",
        timeframe=Timeframe.M1,
        start_time=start,
        end_time=datetime(2026, 9, 1, 9, 16, tzinfo=timezone.utc),
    )
    assert candles[0].instrument_id == "nifty-front"

    events = [event async for event in feed.stream(instrument_ids=["nifty-front"])]
    assert len(events) == 1
    assert events[0].instrument_id == "nifty-front"
