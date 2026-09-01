"""Deterministic aggregation of canonical market candles."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Iterable

from .models import Candle, Timeframe

_TIMEFRAME_MINUTES = {
    Timeframe.M1: 1,
    Timeframe.M3: 3,
    Timeframe.M5: 5,
    Timeframe.M15: 15,
    Timeframe.M30: 30,
    Timeframe.H1: 60,
    Timeframe.H2: 120,
    Timeframe.H4: 240,
}


def _bucket_start(timestamp: datetime, timeframe: Timeframe) -> datetime:
    if timestamp.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    if timeframe in (Timeframe.D1, Timeframe.W1):
        utc = timestamp.astimezone(timezone.utc)
        if timeframe is Timeframe.D1:
            return utc.replace(hour=0, minute=0, second=0, microsecond=0)
        day_start = utc.replace(hour=0, minute=0, second=0, microsecond=0)
        return day_start - timedelta(days=day_start.weekday())

    utc = timestamp.astimezone(timezone.utc)
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    minutes = _TIMEFRAME_MINUTES[timeframe]
    elapsed = int((utc - epoch).total_seconds() // 60)
    return epoch + timedelta(minutes=(elapsed // minutes) * minutes)


def aggregate_candles(candles: Iterable[Candle], timeframe: Timeframe) -> list[Candle]:
    """Aggregate canonical lower-timeframe candles into canonical OHLCV candles."""
    grouped: dict[tuple[str, datetime], list[Candle]] = defaultdict(list)
    for candle in candles:
        grouped[(candle.instrument_id, _bucket_start(candle.timestamp, timeframe))].append(candle)

    result: list[Candle] = []
    for (instrument_id, start), rows in sorted(grouped.items(), key=lambda item: item[0]):
        rows.sort(key=lambda row: row.timestamp)
        bar = Candle(
            instrument_id=instrument_id,
            timestamp=start,
            timeframe=timeframe,
            open=rows[0].open,
            high=max(row.high for row in rows),
            low=min(row.low for row in rows),
            close=rows[-1].close,
            volume=sum((row.volume for row in rows), Decimal("0")),
        )
        result.append(bar.validate_ohlc())
    return result
