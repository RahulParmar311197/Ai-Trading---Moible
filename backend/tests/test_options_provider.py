from datetime import date
from decimal import Decimal

import httpx
import pytest

from app.options.provider import OptionChainProviderError, UpstoxOptionChainProvider


EXPIRY = date(2026, 9, 24)
UNDERLYING = "NSE_INDEX|Nifty 50"
OPTION_KEY = "NSE_FO|12345"


def _chain_payload(*, market_data: dict | None = None) -> dict:
    market = {
        "bid_price": 100,
        "ask_price": 101,
        "ltp": 100.5,
        "volume": 1000,
        "oi": 5000,
    }
    if market_data is not None:
        market = market_data
    return {
        "status": "success",
        "data": [
            {
                "expiry": EXPIRY.isoformat(),
                "strike_price": 25000,
                "underlying_key": UNDERLYING,
                "call_options": {
                    "instrument_key": OPTION_KEY,
                    "market_data": market,
                    "option_greeks": {"iv": 20, "delta": 0.5, "gamma": 0.01, "theta": -5, "vega": 10},
                },
            }
        ],
    }


def _contracts_payload() -> dict:
    return {
        "status": "success",
        "data": [
            {
                "instrument_key": OPTION_KEY,
                "instrument_type": "CE",
                "expiry": EXPIRY.isoformat(),
                "lot_size": 75,
                "underlying_key": UNDERLYING,
                "strike_price": 25000,
                "trading_symbol": "NIFTY 25000 CE 24 SEP 26",
            }
        ],
    }


@pytest.mark.asyncio
async def test_upstox_provider_maps_complete_quote_and_metadata():
    calls = []

    async def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        payload = _chain_payload() if request.url.path.endswith("/option/chain") else _contracts_payload()
        return httpx.Response(200, json=payload, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        chain = await UpstoxOptionChainProvider("token", client=client).get_option_chain(UNDERLYING, EXPIRY)

    assert calls == ["/v2/option/chain", "/v2/option/contract"]
    contract = chain.contracts[0]
    assert contract.symbol == "NIFTY 25000 CE 24 SEP 26"
    assert contract.lot_size == 75
    assert contract.iv == Decimal("0.2")
    assert contract.ltp == Decimal("100.5")


@pytest.mark.asyncio
async def test_upstox_provider_rejects_missing_required_quote_field():
    market = {"bid_price": 100, "ask_price": 101, "volume": 1000, "oi": 5000}

    async def handler(request: httpx.Request) -> httpx.Response:
        payload = _chain_payload(market_data=market) if request.url.path.endswith("/option/chain") else _contracts_payload()
        return httpx.Response(200, json=payload, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(OptionChainProviderError, match="market data is incomplete"):
            await UpstoxOptionChainProvider("token", client=client).get_option_chain(UNDERLYING, EXPIRY)


@pytest.mark.asyncio
async def test_upstox_provider_rejects_missing_contract_metadata():
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/option/chain"):
            return httpx.Response(200, json=_chain_payload(), request=request)
        payload = {"status": "success", "data": []}
        return httpx.Response(200, json=payload, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(OptionChainProviderError, match="metadata is missing"):
            await UpstoxOptionChainProvider("token", client=client).get_option_chain(UNDERLYING, EXPIRY)
