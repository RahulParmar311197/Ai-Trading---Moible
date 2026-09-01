from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.market.models import Candle, Instrument, InstrumentType, Timeframe


def test_instrument_model() -> None:
    instrument = Instrument(
        id="nse-nifty",
        symbol="NIFTY",
        exchange="NSE",
        market="equity_derivatives",
        instrument_type=InstrumentType.FUTURE,
    )
    assert instrument.symbol == "NIFTY"
    assert instrument.active is True


def test_candle_accepts_valid_ohlc() -> None:
    candle = Candle(
        instrument_id="nse-nifty",
        timestamp=datetime(2026, 9, 1, 9, 15, tzinfo=timezone.utc),
        timeframe=Timeframe.M15,
        open=Decimal("25000"),
        high=Decimal("25050"),
        low=Decimal("24980"),
        close=Decimal("25030"),
    )
    assert candle.validate_ohlc() is candle


def test_candle_rejects_invalid_ohlc() -> None:
    candle = Candle(
        instrument_id="nse-nifty",
        timestamp=datetime(2026, 9, 1, 9, 15, tzinfo=timezone.utc),
        timeframe=Timeframe.M15,
        open=Decimal("25000"),
        high=Decimal("24900"),
        low=Decimal("24980"),
        close=Decimal("25030"),
    )
    with pytest.raises(ValueError):
        candle.validate_ohlc()


def test_option_type_is_constrained() -> None:
    with pytest.raises(ValidationError):
        Instrument(
            id="bad-option",
            symbol="NIFTY",
            exchange="NSE",
            market="options",
            instrument_type=InstrumentType.OPTION,
            option_type="INVALID",
        )
