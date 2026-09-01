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


def normalize_upstox_ltp(
    *,
    instrument_id: str,
    price: Any,
    timestamp_ms: int,
) -> MarketEvent:
    """Normalize an Upstox LTPC price update into the canonical event shape.

    A single LTPC tick does not contain OHLC. The canonical event therefore
    uses the observed price for OHLC until candle aggregation supplies a real
    bar. This keeps the provider boundary explicit and prevents fabricated
    high/low values from entering the normalizer.
    """
    if not instrument_id:
        raise UpstoxNormalizationError("instrument_id is required")
    if timestamp_ms <= 0:
        raise UpstoxNormalizationError("timestamp_ms must be positive")
    value = _number(price)
    if value <= 0:
        raise UpstoxNormalizationError("price must be positive")
    timestamp = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
    return MarketEvent(
        instrument_id=instrument_id,
        timestamp=timestamp,
        timeframe=Timeframe.TICK,
        open=value,
        high=value,
        low=value,
        close=value,
        volume=Decimal("0"),
    )
