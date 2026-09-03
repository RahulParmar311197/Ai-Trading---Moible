from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient

import app.main as main
from app.options.models import OptionChain, OptionContract, OptionType
from app.options.provider import UnconfiguredOptionChainProvider


class FakeOptionChainProvider:
    async def get_option_chain(self, underlying: str, expiry: date | None = None) -> OptionChain:
        assert expiry is not None
        return OptionChain(
            underlying=underlying,
            as_of=datetime(2026, 9, 3, tzinfo=timezone.utc),
            contracts=(
                OptionContract(
                    symbol="NIFTY26SEP25000CE",
                    underlying=underlying,
                    expiry=expiry,
                    strike=Decimal("25000"),
                    option_type=OptionType.CALL,
                    lot_size=75,
                    bid=Decimal("100"),
                    ask=Decimal("101"),
                    ltp=Decimal("100.5"),
                ),
            ),
        )


def test_option_chain_endpoint_uses_provider_during_lifespan(monkeypatch):
    provider = FakeOptionChainProvider()
    monkeypatch.setattr(main, "_build_option_chain_provider", lambda: provider)

    with TestClient(main.app) as client:
        response = client.get(
            "/api/v1/options/chain",
            params={"underlying": "NIFTY", "expiry": "2026-09-24"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["underlying"] == "NIFTY"
    assert body["contracts"][0]["symbol"] == "NIFTY26SEP25000CE"
    assert body["contracts"][0]["lot_size"] == 75


def test_option_chain_endpoint_fails_closed_when_provider_unconfigured(monkeypatch):
    monkeypatch.setattr(main, "_build_option_chain_provider", UnconfiguredOptionChainProvider)

    with TestClient(main.app) as client:
        response = client.get(
            "/api/v1/options/chain",
            params={"underlying": "NIFTY", "expiry": "2026-09-24"},
        )

    assert response.status_code == 503
