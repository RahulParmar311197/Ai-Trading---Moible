import pytest

from app.brokers.order_config import (
    BrokerInstrument,
    ExchangeSegment,
    InstrumentResolver,
    ProductType,
)


def test_resolves_canonical_symbol_to_provider_security_id() -> None:
    resolver = InstrumentResolver(
        (
            BrokerInstrument(
                canonical_symbol="NIFTY",
                provider_symbol="99926000",
                exchange_segment=ExchangeSegment.NSE_FNO,
                product_type=ProductType.INTRADAY,
            ),
        )
    )
    instrument = resolver.resolve(" nifty ")
    assert instrument.provider_symbol == "99926000"
    assert instrument.exchange_segment is ExchangeSegment.NSE_FNO


def test_unknown_instrument_is_rejected_instead_of_falling_back() -> None:
    resolver = InstrumentResolver()
    with pytest.raises(KeyError, match="instrument mapping not configured"):
        resolver.resolve("NIFTY")


def test_duplicate_mapping_is_rejected() -> None:
    item = BrokerInstrument("NIFTY", "123", ExchangeSegment.NSE_FNO)
    resolver = InstrumentResolver((item,))
    with pytest.raises(ValueError, match="duplicate instrument mapping"):
        resolver.add(BrokerInstrument("nifty", "456", ExchangeSegment.NSE_FNO))
