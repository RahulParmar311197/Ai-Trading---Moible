import pytest

from app.main import app


@pytest.mark.asyncio
async def test_startup_without_live_market_config_is_degraded():
    async with app.router.lifespan_context(app):
        assert app.state.market_data_startup_error == "Live market data is not configured"


@pytest.mark.asyncio
async def test_startup_wires_provider_runner_to_redis_publisher(monkeypatch):
    class FakeFeed:
        async def stream(self, instrument_ids):
            if False:
                yield None

    class FakeRedis:
        pass

    monkeypatch.setattr("app.main.get_market_data_feed", lambda: FakeFeed())
    monkeypatch.setattr("app.main.get_redis_client", lambda: FakeRedis())
    monkeypatch.setattr("app.main.settings.market_data_provider", "upstox")
    monkeypatch.setattr("app.main.settings.market_data_instrument_ids", "NSE_EQ|TEST")

    async with app.router.lifespan_context(app):
        assert app.state.market_data_feed is not None
        assert app.state.market_data_publisher.redis.__class__ is FakeRedis
        assert app.state.market_data_runner.publish == app.state.market_data_publisher.publish
        assert app.state.market_data_runner_task is not None
