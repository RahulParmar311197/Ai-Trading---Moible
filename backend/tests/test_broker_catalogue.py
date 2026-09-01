import pytest

from app.brokers.catalogue import InstrumentCatalogueError, dhan_catalogue, resolver_from_catalogue, upstox_catalogue
from app.brokers.order_config import ExchangeSegment, OrderValidity, ProductType


def test_upstox_catalogue_maps_stable_instrument_key() -> None:
    instruments = upstox_catalogue(
        [
            {
                "segment": "NSE_FO",
                "instrument_key": "NSE_FO|12345",
                "trading_symbol": "NIFTY25JAN25000CE",
                "lot_size": 75,
            }
        ],
        product_type=ProductType.INTRADAY,
        validity=OrderValidity.IOC,
    )
    item = instruments[0]
    assert item.canonical_symbol == "NIFTY25JAN25000CE"
    assert item.provider_symbol == "NSE_FO|12345"
    assert item.exchange_segment is ExchangeSegment.NSE_FNO
    assert item.lot_size == 75
    assert item.validity is OrderValidity.IOC


def test_dhan_catalogue_maps_security_id_and_segment() -> None:
    instruments = dhan_catalogue(
        [
            {
                "SEM_EXM_EXCH_ID": "NSE",
                "SEM_SEGMENT": "D",
                "SEM_SMST_SECURITY_ID": "123456",
                "SEM_TRADING_SYMBOL": "NIFTY",
                "SEM_LOT_UNITS": "75",
            }
        ]
    )
    item = instruments[0]
    assert item.provider_symbol == "123456"
    assert item.exchange_segment is ExchangeSegment.NSE_FNO
    assert item.lot_size == 75


def test_unsupported_dhan_segment_is_rejected() -> None:
    with pytest.raises(InstrumentCatalogueError, match="unsupported Dhan exchange/segment"):
        dhan_catalogue(
            [
                {
                    "SEM_EXM_EXCH_ID": "MCX",
                    "SEM_SEGMENT": "M",
                    "SEM_SMST_SECURITY_ID": "1",
                    "SEM_TRADING_SYMBOL": "GOLD",
                    "SEM_LOT_UNITS": "1",
                }
            ]
        )


def test_catalogue_resolver_rejects_duplicate_canonical_symbols() -> None:
    rows = [
        {"segment": "NSE_EQ", "instrument_key": "NSE_EQ|1", "trading_symbol": "ABC", "lot_size": 1},
        {"segment": "NSE_EQ", "instrument_key": "NSE_EQ|2", "trading_symbol": "ABC", "lot_size": 1},
    ]
    with pytest.raises(ValueError, match="duplicate instrument mapping"):
        resolver_from_catalogue(upstox_catalogue(rows))
