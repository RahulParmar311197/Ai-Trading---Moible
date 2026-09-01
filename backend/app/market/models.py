"""Canonical market-data models used across providers and strategies."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class InstrumentType(StrEnum):
    EQUITY = "equity"
    ETF = "etf"
    FUTURE = "future"
    OPTION = "option"
    FOREX = "forex"
    CRYPTO = "crypto"
    COMMODITY = "commodity"


class Timeframe(StrEnum):
    """Canonical candle intervals plus the non-aggregated tick event interval."""

    TICK = "tick"
    M1 = "1m"
    M3 = "3m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H2 = "2h"
    H4 = "4h"
    D1 = "1D"
    W1 = "1W"


class Instrument(BaseModel):
    id: str
    symbol: str
    exchange: str
    market: str
    instrument_type: InstrumentType
    underlying: str | None = None
    expiry: datetime | None = None
    strike: Decimal | None = None
    option_type: str | None = Field(default=None, pattern="^(CE|PE)$")
    lot_size: int | None = Field(default=None, gt=0)
    tick_size: Decimal | None = Field(default=None, gt=0)
    currency: str = "INR"
    active: bool = True


class Candle(BaseModel):
    instrument_id: str
    timestamp: datetime
    timeframe: Timeframe
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal = Decimal("0")

    def validate_ohlc(self) -> "Candle":
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("Invalid OHLC relationship")
        if self.low > self.high:
            raise ValueError("Candle low cannot exceed high")
        return self


class MarketEvent(Candle):
    """Canonical event envelope; provider-specific fields are intentionally excluded."""

    exchange: str | None = None
    session: str | None = None
    bid: Decimal | None = None
    ask: Decimal | None = None
    spread: Decimal | None = None
    open_interest: Decimal | None = None
