from datetime import date

import httpx
import pytest

from app.options.provider import OptionChainProviderError, UpstoxOptionChainProvider


def test_upstox_option_chain_maps_market_data_and_percentage_iv(monkeypatch):
    response = {
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

    async def fake_get(*args, **kwargs):
        assert kwargs["params"] == {"instrument_key": "NSE_INDEX|Nifty 50", "expiry_date": "2026-09-24"}
        assert kwargs["headers"]["Authorization"] == "Bearer token"
        return httpx.Response(200, json=response, request=httpx.Request("GET", "https://api.upstox.com/v2/option/chain"))

    client = httpx.AsyncClient()
    monkeypatch.setattr(client, "get", fake_get)
    provider = UpstoxOptionChainProvider("token", client=client)

    import asyncio
    chain = asyncio.run(provider.get_option_chain("NSE_INDEX|Nifty 50", date(2026, 9, 24)))
    asyncio.run(client.aclose())

    assert len(chain.contracts) == 2
    assert chain.contracts[0].iv == pytest.approx(0.2)
    assert chain.contracts[0].lot_size == 1
    assert chain.contracts[1].delta == pytest.approx(-0.5)


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
