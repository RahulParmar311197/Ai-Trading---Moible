from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.market.aggregation import aggregate_candles
from app.market.models import Candle, Timeframe


def candle(ts: str, open_: str, high: str, low: str, close: str, volume: str) -> Candle:
    return Candle(
        instrument_id="NIFTY",
        timestamp=datetime.fromisoformat(ts).replace(tzinfo=timezone.utc),
        timeframe=Timeframe.M1,
        open=Decimal(open_), high=Decimal(high), low=Decimal(low),
        close=Decimal(close), volume=Decimal(volume),
    )


def test_aggregate_candles_returns_canonical_5m_candle():
    rows = [
        candle("2026-09-01T10:01:00", "100", "105", "99", "103", "10"),
        candle("2026-09-01T10:02:00", "103", "107", "102", "106", "20"),
        candle("2026-09-01T10:03:00", "106", "108", "104", "105", "30"),
    ]
    result = aggregate_candles(rows, Timeframe.M5)
    assert result == [Candle(
        instrument_id="NIFTY",
        timestamp=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
        timeframe=Timeframe.M5,
        open=Decimal("100"), high=Decimal("108"), low=Decimal("99"),
        close=Decimal("105"), volume=Decimal("60"),
    )]


def test_aggregate_candles_supports_daily_and_weekly_buckets():
    row = candle("2026-09-01T10:01:00", "100", "105", "99", "103", "10")
    daily = aggregate_candles([row], Timeframe.D1)[0]
    weekly = aggregate_candles([row], Timeframe.W1)[0]
    assert daily.timestamp == datetime(2026, 9, 1, tzinfo=timezone.utc)
    assert weekly.timestamp == datetime(2026, 8, 31, tzinfo=timezone.utc)


def test_aggregate_candles_rejects_naive_timestamps():
    row = Candle(
        instrument_id="NIFTY", timestamp=datetime(2026, 9, 1, 10, 1),
        timeframe=Timeframe.M1, open=Decimal("1"), high=Decimal("1"),
        low=Decimal("1"), close=Decimal("1"), volume=Decimal("0"),
    )
    with pytest.raises(ValueError, match="timezone-aware"):
        aggregate_candles([row], Timeframe.M5)
