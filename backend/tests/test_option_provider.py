from datetime import date
from decimal import Decimal

import httpx
import pytest

from app.options.provider import OptionChainProviderError, UpstoxOptionChainProvider


def test_upstox_option_chain_maps_market_data_and_contract_metadata(monkeypatch):
    chain_response = {
        "status": "success",
        "data": [
            {
                "expiry": "2026-09-24",
                "strike_price": 25000,
                "underlying_key": "NSE_INDEX|Nifty 50",
                "call_options": {
                    "instrument_key": "NSE_FO|123",
                    "market_data": {
                        "ltp": 101.0,
                        "volume": 1000,
                        "oi": 5000,
                        "bid_price": 100.0,
                        "ask_price": 102.0,
                    },
                    "option_greeks": {
                        "delta": 0.5,
                        "gamma": 0.01,
                        "theta": -2.0,
                        "vega": 10.0,
                        "iv": 20.0,
                    },
                },
                "put_options": {
                    "instrument_key": "NSE_FO|124",
                    "market_data": {
                        "ltp": 99.0,
                        "volume": 900,
                        "oi": 4000,
                        "bid_price": 98.0,
                        "ask_price": 100.0,
                    },
                    "option_greeks": {"delta": -0.5, "iv": 22.0},
                },
            }
        ],
    }
    contract_response = {
        "status": "success",
        "data": [
            {
                "instrument_key": "NSE_FO|123",
                "trading_symbol": "NIFTY 25000 CE 24 SEP 26",
                "lot_size": 65,
                "instrument_type": "CE",
                "underlying_key": "NSE_INDEX|Nifty 50",
                "strike_price": 25000,
                "expiry": "2026-09-24",
            },
            {
                "instrument_key": "NSE_FO|124",
                "trading_symbol": "NIFTY 25000 PE 24 SEP 26",
                "lot_size": 65,
                "instrument_type": "PE",
                "underlying_key": "NSE_INDEX|Nifty 50",
                "strike_price": 25000,
                "expiry": "2026-09-24",
            },
        ],
    }

    async def fake_get(url, **kwargs):
        assert kwargs["params"] == {"instrument_key": "NSE_INDEX|Nifty 50", "expiry_date": "2026-09-24"}
        assert kwargs["headers"]["Authorization"] == "Bearer token"
        if url.endswith("/option/chain"):
            payload = chain_response
        else:
            assert url.endswith("/option/contract")
            payload = contract_response
        return httpx.Response(200, json=payload, request=httpx.Request("GET", url))

    client = httpx.AsyncClient()
    monkeypatch.setattr(client, "get", fake_get)
    provider = UpstoxOptionChainProvider("token", client=client)

    import asyncio
    chain = asyncio.run(provider.get_option_chain("NSE_INDEX|Nifty 50", date(2026, 9, 24)))
    asyncio.run(client.aclose())

    assert len(chain.contracts) == 2
    assert chain.contracts[0].symbol == "NIFTY 25000 CE 24 SEP 26"
    assert chain.contracts[0].iv == Decimal("0.2")
    assert chain.contracts[0].lot_size == 65
    assert chain.contracts[1].symbol == "NIFTY 25000 PE 24 SEP 26"
    assert chain.contracts[1].delta == Decimal("-0.5")


def test_upstox_option_chain_requires_explicit_expiry():
    provider = UpstoxOptionChainProvider("token")
    with pytest.raises(ValueError, match="expiry is required"):
        import asyncio
        asyncio.run(provider.get_option_chain("NSE_INDEX|Nifty 50"))


def test_upstox_option_chain_sanitizes_http_errors(monkeypatch):
    async def fake_get(*args, **kwargs):
        raise httpx.ConnectError("private network detail")

    client = httpx.AsyncClient()
    monkeypatch.setattr(client, "get", fake_get)
    provider = UpstoxOptionChainProvider("token", client=client)
    with pytest.raises(OptionChainProviderError, match="request failed") as exc_info:
        import asyncio
        asyncio.run(provider.get_option_chain("NSE_INDEX|Nifty 50", date(2026, 9, 24)))
    asyncio.run(client.aclose())
    assert "private network detail" not in str(exc_info.value)


def test_upstox_option_chain_rejects_missing_contract_metadata(monkeypatch):
    responses = [
        {"status": "success", "data": [{
            "expiry": "2026-09-24",
            "strike_price": 25000,
            "underlying_key": "NSE_INDEX|Nifty 50",
            "call_options": {"instrument_key": "NSE_FO|123", "market_data": {}, "option_greeks": {}},
        }]},
        {"status": "success", "data": []},
    ]

    async def fake_get(url, **kwargs):
        return httpx.Response(200, json=responses.pop(0), request=httpx.Request("GET", url))

    client = httpx.AsyncClient()
    monkeypatch.setattr(client, "get", fake_get)
    provider = UpstoxOptionChainProvider("token", client=client)
    with pytest.raises(OptionChainProviderError, match="missing"):
        import asyncio
        asyncio.run(provider.get_option_chain("NSE_INDEX|Nifty 50", date(2026, 9, 24)))
    asyncio.run(client.aclose())
