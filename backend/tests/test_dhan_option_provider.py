from datetime import date
from decimal import Decimal

import httpx
import pytest

from app.brokers.order_config import (
    BrokerInstrument,
    ExchangeSegment,
    OptionInstrumentMetadata,
    OptionType as InstrumentOptionType,
)
from app.options.dhan_provider import DhanOptionChainProvider
from app.options.provider import OptionChainProviderError


def _instrument(security_id: str, symbol: str, option_type: InstrumentOptionType) -> BrokerInstrument:
    return BrokerInstrument(
        canonical_symbol=symbol,
        provider_symbol=security_id,
        exchange_segment=ExchangeSegment.NSE_FNO,
        lot_size=75,
        option_metadata=OptionInstrumentMetadata(
            expiry=date(2026, 9, 24), strike=Decimal("25000"), option_type=option_type
        ),
    )


def _provider(payload, clock=lambda: 100.0):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["access-token"] == "token"
        assert request.headers["client-id"] == "client"
        assert request.json() == {
            "UnderlyingScrip": 13,
            "UnderlyingSeg": "IDX_I",
            "Expiry": "2026-09-24",
        }
        return httpx.Response(200, json=payload)

    return DhanOptionChainProvider(
        "client", "token", underlying_segment="IDX_I",
        catalogue={
            "42528": _instrument("42528", "NIFTY24SEP25000CE", InstrumentOptionType.CALL),
            "42529": _instrument("42529", "NIFTY24SEP25000PE", InstrumentOptionType.PUT),
        },
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        clock=clock,
    )


@pytest.mark.asyncio
async def test_dhan_option_chain_maps_quotes_and_catalogue_metadata():
    provider = _provider({
        "status": "success",
        "data": {"oc": {"25000.000000": {
            "ce": {"security_id": 42528, "last_price": 134, "oi": 3786445, "volume": 117567970,
                   "top_bid_price": 133.55, "top_ask_price": 134, "implied_volatility": 9.789,
                   "greeks": {"delta": 0.53871, "theta": -15.15, "gamma": 0.00132, "vega": 12.18}},
            "pe": {"security_id": 42529, "last_price": 132.8, "oi": 3096145, "volume": 157009970,
                   "top_bid_price": 132.45, "top_ask_price": 132.75, "implied_volatility": 11.93,
                   "greeks": {"delta": -0.46732, "theta": -10.61, "gamma": 0.00109, "vega": 12.20}},
        }}}
    })
    chain = await provider.get_option_chain("13", date(2026, 9, 24))
    assert len(chain.contracts) == 2
    assert chain.contracts[0].symbol == "NIFTY24SEP25000CE"
    assert chain.contracts[0].lot_size == 75
    assert chain.contracts[0].iv == Decimal("0.09789")


@pytest.mark.asyncio
async def test_dhan_option_chain_rejects_missing_catalogue_metadata():
    provider = _provider({"status": "success", "data": {"oc": {"25000": {
        "ce": {"security_id": 99999, "last_price": 100, "oi": 1, "volume": 1,
               "top_bid_price": 99, "top_ask_price": 101, "implied_volatility": 10, "greeks": {}},
    }}}})
    with pytest.raises(OptionChainProviderError, match="catalogue metadata"):
        await provider.get_option_chain("13", date(2026, 9, 24))


@pytest.mark.asyncio
async def test_dhan_option_chain_enforces_three_second_keyed_cooldown():
    now = [100.0]
    provider = _provider({"status": "success", "data": {"oc": {"25000": {
        "ce": {"security_id": 42528, "last_price": 100, "oi": 1, "volume": 1,
               "top_bid_price": 99, "top_ask_price": 101, "implied_volatility": 10, "greeks": {}},
    }}}}, clock=lambda: now[0])
    await provider.get_option_chain("13", date(2026, 9, 24))
    with pytest.raises(OptionChainProviderError, match="rate limited"):
        await provider.get_option_chain("13", date(2026, 9, 24))
    now[0] += 3.0
    await provider.get_option_chain("13", date(2026, 9, 24))
