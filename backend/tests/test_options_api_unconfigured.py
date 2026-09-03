from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app


def test_option_chain_endpoint_returns_503_when_unconfigured(monkeypatch):
    monkeypatch.setattr(app.state, "option_chain_provider", SimpleNamespace(), raising=False)

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/options/chain",
            params={"underlying": "NIFTY", "expiry": "2026-09-24"},
        )

    assert response.status_code == 503
