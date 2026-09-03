from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app
from app.options.models import OptionChain, OptionContract


class FakeOptionChainProvider:
    async def get_chain(self, underlying: str, expiry: date) -> OptionChain:
        return OptionChain(
            underlying=underlying,
            expiry=expiry,
            contracts=(
                OptionContract(
                    symbol="NIFTY26SEP25000CE",
                    underlying=underlying,
                    expiry=expiry,
                    strike=Decimal("25000"),
                    option_type="CE",
                    lot_size=75,
                    bid=Decimal("100"),
                    ask=Decimal("101"),
                    ltp=Decimal("100.5"),
                ),
            ),
        )


def test_option_chain_endpoint_uses_provider(monkeypatch):
    provider = FakeOptionChainProvider()
    monkeypatch.setattr(
        app.state,
        "option_chain_provider",
        provider,
        raising=False,
    )

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/options/chain",
            params={"underlying": "NIFTY", "expiry": "2026-09-24"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["underlying"] == "NIFTY"
    assert body["expiry"] == "2026-09-24"
    assert body["contracts"][0]["symbol"] == "NIFTY26SEP25000CE"
    assert body["contracts"][0]["lot_size"] == 75


def test_option_chain_endpoint_returns_503_when_unconfigured(monkeypatch):
    monkeypatch.setattr(
        app.state,
        "option_chain_provider",
        SimpleNamespace(),
        raising=False,
    )

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/options/chain",
            params={"underlying": "NIFTY", "expiry": "2026-09-24"},
        )

    assert response.status_code == 503
