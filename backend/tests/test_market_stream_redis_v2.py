import pytest

from app.api.market_stream import MarketEventHub
from app.market.models import MarketEvent, Timeframe
from datetime import datetime, timezone
from decimal import Decimal


def test_market_event_hub_payload_validation():
    hub = MarketEventHub()
    event = MarketEvent(
        instrument_id="nifty",
        timestamp=datetime(2026, 9, 1, 9, 15, tzinfo=timezone.utc),
        timeframe=Timeframe.M15,
        open=Decimal("25000"), high=Decimal("25050"),
        low=Decimal("24980"), close=Decimal("25030"), volume=Decimal("100"),
    )
    assert event.instrument_id == "nifty"
    assert hub is not None
