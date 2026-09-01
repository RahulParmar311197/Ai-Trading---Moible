import asyncio
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.api.market_stream import MarketEventHub
from app.market.models import MarketEvent, Timeframe


@pytest.mark.asyncio
async def test_market_event_hub_publishes_normalized_events() -> None:
    hub = MarketEventHub()
    event = MarketEvent(
        instrument_id="nifty-front",
        timestamp=datetime(2026, 9, 1, 9, 15, tzinfo=timezone.utc),
        timeframe=Timeframe.M15,
        open=Decimal("25000"), high=Decimal("25050"),
        low=Decimal("24980"), close=Decimal("25030"), volume=Decimal("100"),
    )

    stream = hub.subscribe("nifty-front")
    task = asyncio.create_task(stream.__anext__())
    await asyncio.sleep(0)
    await hub.publish(event)
    payload = await asyncio.wait_for(task, timeout=1)

    assert '"instrument_id":"nifty-front"' in payload
    await stream.aclose()
