from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.market.models import MarketEvent, Timeframe
from app.market.provider_runtime import ProviderMarketRunner
from app.market.quality import MarketDataQualityError


@pytest.mark.asyncio
async def test_provider_event_reaches_publisher_after_quality_gate():
    published = []
    now = datetime.now(timezone.utc)

    class FakeFeed:
        async def stream(self, instrument_ids):
            yield MarketEvent(
                instrument_id="NIFTY",
                timestamp=now,
                timeframe=Timeframe.M1,
                open=Decimal("24990"),
                high=Decimal("25010"),
                low=Decimal("24980"),
                close=Decimal("25000"),
                volume=Decimal("100"),
            )

    async def publish(event):
        published.append(event)

    runner = ProviderMarketRunner(FakeFeed(), publish)
    await runner.run(["NIFTY"])

    assert len(published) == 1
    assert published[0].instrument_id == "NIFTY"
    assert published[0].close == Decimal("25000")


@pytest.mark.asyncio
async def test_invalid_provider_event_is_blocked_before_publisher():
    published = []
    now = datetime.now(timezone.utc)

    class FakeFeed:
        async def stream(self, instrument_ids):
            yield MarketEvent(
                instrument_id="NIFTY",
                timestamp=now - timedelta(seconds=60),
                timeframe=Timeframe.M1,
                open=Decimal("24990"),
                high=Decimal("25010"),
                low=Decimal("24980"),
                close=Decimal("25000"),
                volume=Decimal("100"),
            )

    async def publish(event):
        published.append(event)

    runner = ProviderMarketRunner(FakeFeed(), publish)

    with pytest.raises(MarketDataQualityError, match="stale"):
        await runner.run(["NIFTY"])

    assert published == []
