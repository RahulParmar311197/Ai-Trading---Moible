import pytest

from app.main import app


@pytest.mark.asyncio
async def test_startup_without_live_market_config_is_degraded():
    async with app.router.lifespan_context(app):
        assert app.state.market_data_startup_error == "Live market data is not configured"
