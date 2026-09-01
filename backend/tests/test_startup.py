import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_is_degraded_when_live_market_data_is_unconfigured(monkeypatch):
    monkeypatch.setattr(app.state, "market_data_startup_error", "Live market data is not configured")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "degraded"}
