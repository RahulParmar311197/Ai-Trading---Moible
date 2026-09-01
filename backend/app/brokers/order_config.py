from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ExchangeSegment(StrEnum):
    NSE_EQ = "NSE_EQ"
    NSE_FNO = "NSE_FNO"
    BSE_EQ = "BSE_EQ"
    BSE_FNO = "BSE_FNO"


class ProductType(StrEnum):
    INTRADAY = "INTRADAY"
    DELIVERY = "DELIVERY"
    MARGIN = "MARGIN"


class OrderValidity(StrEnum):
    DAY = "DAY"
    IOC = "IOC"


@dataclass(frozen=True, slots=True)
class BrokerInstrument:
    canonical_symbol: str
    provider_symbol: str
    exchange_segment: ExchangeSegment
    product_type: ProductType = ProductType.INTRADAY
    validity: OrderValidity = OrderValidity.DAY
    lot_size: int = 1

    def __post_init__(self) -> None:
        if not self.canonical_symbol.strip() or not self.provider_symbol.strip():
            raise ValueError("instrument symbols must be non-empty")
        if self.lot_size < 1:
            raise ValueError("lot_size must be positive")


class InstrumentResolver:
    """Deterministic provider-symbol resolver; no network or credentials."""

    def __init__(self, instruments: tuple[BrokerInstrument, ...] = ()) -> None:
        self._by_canonical = {item.canonical_symbol.upper(): item for item in instruments}
        if len(self._by_canonical) != len(instruments):
            raise ValueError("duplicate instrument mapping")

    def resolve(self, canonical_symbol: str) -> BrokerInstrument:
        key = canonical_symbol.strip().upper()
        if not key:
            raise ValueError("canonical symbol must be non-empty")
        try:
            return self._by_canonical[key]
        except KeyError as exc:
            raise KeyError(f"instrument mapping not configured: {key}") from exc

    def add(self, instrument: BrokerInstrument) -> None:
        key = instrument.canonical_symbol.strip().upper()
        if not key:
            raise ValueError("canonical symbol must be non-empty")
        if key in self._by_canonical:
            raise ValueError(f"duplicate instrument mapping: {instrument.canonical_symbol}")
        self._by_canonical[key] = instrument
