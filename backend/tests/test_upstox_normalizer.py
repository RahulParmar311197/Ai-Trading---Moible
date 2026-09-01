from datetime import timezone
from decimal import Decimal

import pytest

from app.market.models import Timeframe
from app.market.upstox_normalizer import UpstoxNormalizationError, normalize_upstox_ltp


def test_normalize_ltp_to_canonical_event():
    event = normalize_upstox_ltp(
        instrument_id="NSE_EQ|INE002A01018",
        price="25030.50",
        timestamp_ms=1788254100000,
    )
    assert event.timeframe == Timeframe.TICK
    assert event.open == Decimal("25030.50")
    assert event.high == event.low == event.close
    assert event.timestamp.tzinfo == timezone.utc


@pytest.mark.parametrize(
    "kwargs",
    [
        {"instrument_id": "", "price": "100", "timestamp_ms": 1788254100000},
        {"instrument_id": "x", "price": "0", "timestamp_ms": 1788254100000},
        {"instrument_id": "x", "price": "100", "timestamp_ms": 0},
    ],
)
def test_invalid_ltp_is_rejected(kwargs):
    with pytest.raises(UpstoxNormalizationError):
        normalize_upstox_ltp(**kwargs)
