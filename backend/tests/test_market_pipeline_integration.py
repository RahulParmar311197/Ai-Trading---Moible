from dataclasses import dataclass

import pytest

from app.market.provider_runtime import ProviderMarketRunner
from app.market.validation import MarketDataQualityError, validate_market_event


@dataclass
class Event:
    instrument_id: str
    timestamp: object
    price: float


@pytest.mark.asyncio
async def test_provider_event_reaches_publisher_after_quality_gate():
    published = []

    async def publish(event):
        published.append(event)

    event = Event("NIFTY", "2026-09-01T10:00:00Z", 25000.0)
    runner = ProviderMarketRunner(lambda: None, publish)

    await runner.handle_event(event)

    assert published == [event]


@pytest.mark.asyncio
async def test_invalid_provider_event_is_blocked_before_publisher():
    published = []

    async def publish(event):
        published.append(event)

    invalid = Event("NIFTY", "2026-09-01T10:00:00Z", -1.0)
    runner = ProviderMarketRunner(lambda: None, publish)

    with pytest.raises(MarketDataQualityError):
        await runner.handle_event(invalid)

    assert published == []
