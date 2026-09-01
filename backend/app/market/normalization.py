"""Provider-neutral validation and normalization for market events."""

from datetime import datetime, timezone
from decimal import Decimal

from .models import Candle, MarketEvent, Timeframe


def normalize_candle(
    *,
    instrument_id: str,
    timestamp: datetime,
    timeframe: Timeframe,
    open: Decimal,
    high: Decimal,
    low: Decimal,
    close: Decimal,
    volume: Decimal = Decimal("0"),
) -> Candle:
    """Create a canonical candle and reject invalid market data."""
    if timestamp.tzinfo is None:
        raise ValueError("Market timestamps must be timezone-aware")
    candle = Candle(
        instrument_id=instrument_id,
        timestamp=timestamp.astimezone(timezone.utc),
        timeframe=timeframe,
        open=open,
        high=high,
        low=low,
        close=close,
        volume=volume,
    )
    return candle.validate_ohlc()


def normalize_event(event: MarketEvent) -> MarketEvent:
    """Normalize an already structured event to UTC and validate OHLC."""
    if event.timestamp.tzinfo is None:
        raise ValueError("Market timestamps must be timezone-aware")
    event.timestamp = event.timestamp.astimezone(timezone.utc)
    return event.validate_ohlc()  # type: ignore[return-value]
