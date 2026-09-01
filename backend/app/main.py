import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.market_data import router as market_data_router
from app.api.market_stream import router as market_stream_router
from app.api.markets import router as markets_router
from app.config import settings
from app.market.provider_runtime import ProviderMarketRunner
from app.market.providers import ProviderConfigurationError, get_market_data_feed


@asynccontextmanager
async def lifespan(app: FastAPI):
    runner_task: asyncio.Task[None] | None = None
    if settings.market_data_provider and settings.configured_market_data_instruments:
        try:
            feed = get_market_data_feed()
            # Publisher wiring is intentionally deferred until the live publisher
            # dependency is configured; startup must never invent a sink.
            app.state.market_data_feed = feed
            app.state.market_data_runner = ProviderMarketRunner(feed, _unconfigured_publisher)
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


async def _unconfigured_publisher(event) -> None:
    raise RuntimeError("Live market publisher is not configured")


app = FastAPI(title="AI Trading Platform API", version="0.1.0", lifespan=lifespan)
app.include_router(markets_router)
app.include_router(market_data_router)
app.include_router(market_stream_router)


@app.get("/health")
def health() -> dict[str, str]:
    status = getattr(app.state, "market_data_startup_error", None)
    return {"status": "ok" if status is None else "degraded"}
