from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.market.models import MarketEvent, Timeframe
from app.market.quality import MarketDataQualityError, validate_event


def event(**overrides):
    values = {
        "instrument_id": "nifty-front",
        "timestamp": datetime(2026, 9, 1, 9, 15, tzinfo=timezone.utc),
        "timeframe": Timeframe.M15,
        "open": Decimal("25000"), "high": Decimal("25050"),
        "low": Decimal("24980"), "close": Decimal("25030"),
        "volume": Decimal("100"),
    }
    values.update(overrides)
    return MarketEvent(**values)


def test_valid_event_passes():
    now = datetime(2026, 9, 1, 9, 15, 20, tzinfo=timezone.utc)
    assert validate_event(event(), now=now) == event()


@pytest.mark.parametrize("overrides", [
    {"volume": Decimal("-1")},
    {"bid": Decimal("25040"), "ask": Decimal("25030")},
    {"bid": Decimal("0")},
])
def test_invalid_market_quality_is_rejected(overrides):
    with pytest.raises(MarketDataQualityError):
        validate_event(event(**overrides), now=datetime(2026, 9, 1, 9, 15, 20, tzinfo=timezone.utc))


def test_stale_event_is_rejected():
    now = datetime(2026, 9, 1, 9, 16, tzinfo=timezone.utc)
    with pytest.raises(MarketDataQualityError, match="stale"):
        validate_event(event(), now=now, max_age=timedelta(seconds=30))


def test_future_event_is_rejected():
    now = datetime(2026, 9, 1, 9, 14, tzinfo=timezone.utc)
    with pytest.raises(MarketDataQualityError, match="future"):
        validate_event(event(), now=now)
