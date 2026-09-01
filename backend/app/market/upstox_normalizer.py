"""Map decoded Upstox V3 feed messages to canonical market events."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.market.models import MarketEvent, Timeframe


class UpstoxNormalizationError(ValueError):
    pass


def _number(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:
        raise UpstoxNormalizationError("Invalid numeric market value") from exc


def normalize_upstox_ltp(*, instrument_id: str, price: Any, timestamp_ms: int, quantity: Any = 0) -> MarketEvent:
    """Normalize an Upstox LTPC update into the canonical tick event."""
    if not instrument_id:
        raise UpstoxNormalizationError("instrument_id is required")
    if timestamp_ms <= 0:
        raise UpstoxNormalizationError("timestamp_ms must be positive")
    value = _number(price)
    volume = _number(quantity)
    if value <= 0:
        raise UpstoxNormalizationError("price must be positive")
    if volume < 0:
        raise UpstoxNormalizationError("quantity cannot be negative")
    timestamp = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
    return MarketEvent(instrument_id=instrument_id, timestamp=timestamp, timeframe=Timeframe.TICK,
                       open=value, high=value, low=value, close=value, volume=volume)


def _field(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    value = getattr(obj, name, default)
    return value() if callable(value) else value


def normalize_upstox_feed_response(response: Any) -> list[MarketEvent]:
    """Extract LTPC from official Upstox V3 FeedResponse-shaped objects."""
    feeds = _field(response, "feeds", {})
    events: list[MarketEvent] = []
    for instrument_id, feed in (feeds.items() if hasattr(feeds, "items") else []):
        ltpc = _field(feed, "ltpc")
        if ltpc is None:
            wrapper = _field(feed, "fullFeed") or _field(feed, "ff")
            for name in ("marketFF", "indexFF"):
                candidate = _field(wrapper, name)
                ltpc = _field(candidate, "ltpc")
                if ltpc is not None:
                    break
        if ltpc is None:
            continue
        price, timestamp = _field(ltpc, "ltp"), _field(ltpc, "ltt")
        if price is None or timestamp is None:
            continue
        events.append(normalize_upstox_ltp(
            instrument_id=str(instrument_id), price=price,
            timestamp_ms=int(timestamp), quantity=_field(ltpc, "ltq", 0)))
    return events
