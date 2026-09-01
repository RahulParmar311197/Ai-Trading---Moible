import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app


@pytest.mark.asyncio
async def test_lifespan_marks_health_degraded_without_live_configuration(monkeypatch):
    monkeypatch.setattr(settings, "market_data_provider", "")
    monkeypatch.setattr(settings, "market_data_instrument_ids", "")

    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "degraded"}


@pytest.mark.asyncio
async def test_health_is_degraded_when_startup_error_is_present(monkeypatch):
    monkeypatch.setattr(app.state, "market_data_startup_error", "provider unavailable")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "degraded"}
