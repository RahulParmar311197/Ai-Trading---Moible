import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.ai import router as ai_router
from app.api.backtest import router as backtest_router
from app.api.market_data import router as market_data_router
from app.api.market_stream import router as market_stream_router
from app.api.markets import router as markets_router
from app.config import settings
from app.market.provider_runtime import ProviderMarketRunner
from app.market.providers import ProviderConfigurationError, get_market_data_feed
from app.market.redis_client import get_redis_client
from app.market.redis_publisher import RedisMarketPublisher


@asynccontextmanager
async def lifespan(app: FastAPI):
    runner_task: asyncio.Task[None] | None = None
    if settings.market_data_provider and settings.configured_market_data_instruments:
        try:
            feed = get_market_data_feed()
            publisher = RedisMarketPublisher(get_redis_client())
            runner = ProviderMarketRunner(feed, publisher.publish)
            app.state.market_data_feed = feed
            app.state.market_data_publisher = publisher
            app.state.market_data_runner = runner
            runner_task = runner.start(settings.configured_market_data_instruments)
            app.state.market_data_runner_task = runner_task
        except ProviderConfigurationError as exc:
            app.state.market_data_startup_error = str(exc)
    else:
        app.state.market_data_startup_error = "Live market data is not configured"

    try:
        yield
    finally:
        if runner_task is not None:
            runner_task.cancel()
            await asyncio.gather(runner_task, return_exceptions=True)


app = FastAPI(title="AI Trading Platform API", version="0.1.0", lifespan=lifespan)
app.include_router(markets_router)
app.include_router(market_data_router)
app.include_router(market_stream_router)
app.include_router(backtest_router)
app.include_router(ai_router)


@app.get("/health")
def health() -> dict[str, str]:
    status = getattr(app.state, "market_data_startup_error", None)
    return {"status": "ok" if status is None else "degraded"}
