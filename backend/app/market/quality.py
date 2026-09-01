"""Provider-neutral market-data freshness and quality checks."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from .models import Candle, MarketEvent


class MarketDataQualityError(ValueError):
    """Raised when a market event fails canonical quality checks."""


def validate_event(event: MarketEvent, *, now: datetime | None = None, max_age: timedelta = timedelta(seconds=30)) -> MarketEvent:
    """Validate OHLC/volume and reject stale or future-dated events."""
    event.validate_ohlc()
    if event.volume < 0:
        raise MarketDataQualityError("Market event volume cannot be negative")
    if event.bid is not None and event.bid <= 0:
        raise MarketDataQualityError("Market event bid must be positive")
    if event.ask is not None and event.ask <= 0:
        raise MarketDataQualityError("Market event ask must be positive")
    if event.bid is not None and event.ask is not None and event.bid > event.ask:
        raise MarketDataQualityError("Market event bid cannot exceed ask")

    reference = now or datetime.now(timezone.utc)
    timestamp = event.timestamp
    if timestamp.tzinfo is None:
        raise MarketDataQualityError("Market event timestamp must be timezone-aware")
    age = reference - timestamp.astimezone(timezone.utc)
    if age < timedelta(0):
        raise MarketDataQualityError("Market event timestamp cannot be in the future")
    if age > max_age:
        raise MarketDataQualityError("Market event is stale")
    return event
