from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date
from decimal import Decimal
from typing import Any

from .order_config import (
    BrokerInstrument,
    ExchangeSegment,
    InstrumentResolver,
    OptionInstrumentMetadata,
    OptionType,
    OrderValidity,
    ProductType,
)


class InstrumentCatalogueError(ValueError):
    """Raised when a provider catalogue row cannot be mapped safely."""


def _required(row: Mapping[str, Any], *names: str) -> str:
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip():
            return str(value).strip()
    raise InstrumentCatalogueError(f"catalogue field missing: {'/'.join(names)}")


def _lot_size(row: Mapping[str, Any], *names: str) -> int:
    raw = _required(row, *names)
    try:
        value = int(float(raw))
    except (TypeError, ValueError) as exc:
        raise InstrumentCatalogueError(f"invalid lot size: {raw}") from exc
    if value < 1:
        raise InstrumentCatalogueError(f"invalid lot size: {value}")
    return value


def _segment(value: str) -> ExchangeSegment:
    normalized = value.strip().upper()
    aliases = {
        "NSE_FO": ExchangeSegment.NSE_FNO,
        "BSE_FO": ExchangeSegment.BSE_FNO,
    }
    if normalized in aliases:
        return aliases[normalized]
    try:
        return ExchangeSegment(normalized)
    except ValueError as exc:
        raise InstrumentCatalogueError(f"unsupported exchange segment: {value}") from exc


def _option_metadata(row: Mapping[str, Any]) -> OptionInstrumentMetadata | None:
    expiry_raw = next((row.get(name) for name in ("SEM_EXPIRY_DATE", "EXPIRY_DATE", "expiry") if row.get(name)), None)
    strike_raw = next((row.get(name) for name in ("SEM_STRIKE_PRICE", "STRIKE_PRICE", "strike") if row.get(name) is not None), None)
    type_raw = next((row.get(name) for name in ("SEM_OPTION_TYPE", "OPTION_TYPE", "option_type") if row.get(name)), None)
    if expiry_raw is None and strike_raw is None and type_raw is None:
        return None
    if expiry_raw is None or strike_raw is None or type_raw is None:
        raise InstrumentCatalogueError("option catalogue metadata is incomplete")
    try:
        expiry = date.fromisoformat(str(expiry_raw)[:10])
        strike = Decimal(str(strike_raw))
        normalized = str(type_raw).strip().upper()
        option_type = {"CE": OptionType.CALL, "CALL": OptionType.CALL, "PE": OptionType.PUT, "PUT": OptionType.PUT}[normalized]
        return OptionInstrumentMetadata(expiry=expiry, strike=strike, option_type=option_type)
    except (KeyError, TypeError, ValueError, ArithmeticError) as exc:
        raise InstrumentCatalogueError("invalid option catalogue metadata") from exc


def upstox_catalogue(
    rows: Iterable[Mapping[str, Any]],
    *,
    product_type: ProductType = ProductType.INTRADAY,
    validity: OrderValidity = OrderValidity.DAY,
) -> tuple[BrokerInstrument, ...]:
    """Convert Upstox BOD JSON records into canonical broker instruments."""
    result: list[BrokerInstrument] = []
    for row in rows:
        provider_symbol = _required(row, "instrument_key")
        canonical_symbol = _required(row, "trading_symbol", "short_name", "name")
        result.append(
            BrokerInstrument(
                canonical_symbol=canonical_symbol,
                provider_symbol=provider_symbol,
                exchange_segment=_segment(_required(row, "segment")),
                product_type=product_type,
                validity=validity,
                lot_size=_lot_size(row, "lot_size", "minimum_lot"),
                option_metadata=_option_metadata(row),
            )
        )
    return tuple(result)


def dhan_catalogue(
    rows: Iterable[Mapping[str, Any]],
    *,
    product_type: ProductType = ProductType.INTRADAY,
    validity: OrderValidity = OrderValidity.DAY,
) -> tuple[BrokerInstrument, ...]:
    """Convert Dhan scrip-master rows into canonical broker instruments."""
    result: list[BrokerInstrument] = []
    segment_map = {
        ("NSE", "E"): ExchangeSegment.NSE_EQ,
        ("NSE", "D"): ExchangeSegment.NSE_FNO,
        ("BSE", "E"): ExchangeSegment.BSE_EQ,
        ("BSE", "D"): ExchangeSegment.BSE_FNO,
    }
    for row in rows:
        exchange = _required(row, "SEM_EXM_EXCH_ID", "EXCH_ID").upper()
        segment_code = _required(row, "SEM_SEGMENT", "SEGMENT").upper()
        try:
            exchange_segment = segment_map[(exchange, segment_code)]
        except KeyError as exc:
            raise InstrumentCatalogueError(
                f"unsupported Dhan exchange/segment: {exchange}/{segment_code}"
            ) from exc
        provider_symbol = _required(row, "SEM_SMST_SECURITY_ID", "SECURITY_ID", "securityId")
        canonical_symbol = _required(row, "SEM_TRADING_SYMBOL", "SYMBOL_NAME", "SM_SYMBOL_NAME")
        result.append(
            BrokerInstrument(
                canonical_symbol=canonical_symbol,
                provider_symbol=provider_symbol,
                exchange_segment=exchange_segment,
                product_type=product_type,
                validity=validity,
                lot_size=_lot_size(row, "SEM_LOT_UNITS", "LOT_SIZE"),
                option_metadata=_option_metadata(row),
            )
        )
    return tuple(result)


def resolver_from_catalogue(instruments: Iterable[BrokerInstrument]) -> InstrumentResolver:
    """Build a resolver and fail atomically on duplicate canonical symbols."""
    return InstrumentResolver(tuple(instruments))
