from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.market.feed import MarketDataFeed
from app.market.models import MarketEvent, Timeframe
from app.market.provider_runtime import ProviderMarketRunner
from app.market.quality import MarketDataQualityError


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
async def test_provider_runner_forwards_validated_events(monkeypatch):
    received = []

    async def publish(event):
        received.append(event)

    monkeypatch.setattr("app.market.provider_runtime.validate_event", lambda event: event)
    await ProviderMarketRunner(FakeFeed(), publish).run(["nifty-front"])
    assert len(received) == 1
    assert received[0].instrument_id == "nifty-front"


@pytest.mark.asyncio
async def test_provider_runner_does_not_publish_quality_failure(monkeypatch):
    received = []

    async def publish(event):
        received.append(event)

    def reject(event):
        raise MarketDataQualityError("stale")

    monkeypatch.setattr("app.market.provider_runtime.validate_event", reject)
    with pytest.raises(MarketDataQualityError):
        await ProviderMarketRunner(FakeFeed(), publish).run(["nifty-front"])
    assert received == []
