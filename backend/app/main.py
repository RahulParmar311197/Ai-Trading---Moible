import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.ai import router as ai_router
from app.api.backtest import router as backtest_router
from app.api.market_data import router as market_data_router
from app.api.market_stream import router as market_stream_router
from app.api.markets import router as markets_router
from app.api.options import router as options_router
from app.api.paper import router as paper_router
from app.brokers.upstox.adapter import UpstoxBroker
from app.config import settings
from app.execution import (
    ControlledExecutionError,
    RiskLimits,
    StaticTradingSessionIdentityProvider,
    TradingSessionError,
    build_execution_runtime,
)
from app.market.provider_runtime import ProviderMarketRunner
from app.market.providers import ProviderConfigurationError, get_market_data_feed
from app.market.redis_client import get_redis_client
from app.market.redis_publisher import RedisMarketPublisher
from app.options.provider import OptionChainProvider, OptionChainProviderError, UnconfiguredOptionChainProvider, UpstoxOptionChainProvider


def _execution_runtime_configured() -> bool:
    return bool(
        settings.execution_broker.strip()
        and settings.trading_session_id.strip()
        and settings.execution_confirmation_phrase.strip()
        and settings.execution_max_order_notional is not None
        and settings.execution_max_position_quantity is not None
        and settings.execution_max_daily_loss is not None
    )


def _build_execution_runtime():
    provider = settings.execution_broker.strip().lower()
    if not _execution_runtime_configured():
        return None, "Controlled execution is not configured"
    if provider != "upstox":
        return None, f"Unsupported execution broker: {provider}"

    if settings.execution_sandbox:
        access_token = settings.upstox_sandbox_access_token
    else:
        access_token = settings.upstox_access_token
    if not access_token.strip():
        return None, "Upstox execution access token is not configured"

    broker = UpstoxBroker(
        access_token,
        sandbox=settings.execution_sandbox,
        allow_live_orders=settings.execution_allow_live_orders,
        allow_sandbox_orders=settings.execution_allow_sandbox_orders,
    )
    runtime = build_execution_runtime(
        broker,
        session_identity_provider=StaticTradingSessionIdentityProvider(settings.trading_session_id),
        risk_limits=RiskLimits(
            max_order_notional=settings.execution_max_order_notional,
            max_position_quantity=settings.execution_max_position_quantity,
            max_daily_loss=settings.execution_max_daily_loss,
        ),
        confirmation_phrase=settings.execution_confirmation_phrase,
        database_url=settings.database_url,
    )
    return runtime, None


def _build_option_chain_provider() -> OptionChainProvider:
    provider = settings.options_provider.strip().lower()
    if not provider:
        return UnconfiguredOptionChainProvider()
    if provider == "upstox":
        access_token = settings.upstox_access_token
        if not access_token.strip():
            raise OptionChainProviderError("Upstox option-chain access token is not configured")
        return UpstoxOptionChainProvider(access_token, timeout=settings.options_timeout_seconds)
    raise OptionChainProviderError(f"Unsupported option-chain provider: {provider}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    runner_task: asyncio.Task[None] | None = None
    execution_runtime = None

    try:
        app.state.option_chain_provider = _build_option_chain_provider()
        app.state.option_chain_startup_error = None
    except OptionChainProviderError as exc:
        app.state.option_chain_provider = UnconfiguredOptionChainProvider()
        app.state.option_chain_startup_error = str(exc)

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
        execution_runtime, execution_error = _build_execution_runtime()
        app.state.execution_runtime = execution_runtime
        if execution_error is not None:
            app.state.execution_startup_error = execution_error
        else:
            try:
                await execution_runtime.executor.startup()
                await execution_runtime.sessions.establish()
                app.state.execution_startup_error = None
            except (ControlledExecutionError, TradingSessionError) as exc:
                app.state.execution_startup_error = str(exc)
                if execution_runtime is not None:
                    await execution_runtime.executor.shutdown("execution startup failed")
            except Exception as exc:
                app.state.execution_startup_error = f"execution startup failed: {type(exc).__name__}"
                if execution_runtime is not None:
                    await execution_runtime.executor.shutdown("execution startup failed")
        yield
    finally:
        if execution_runtime is not None:
            await execution_runtime.executor.shutdown("application shutdown")
        if runner_task is not None:
            runner_task.cancel()
            await asyncio.gather(runner_task, return_exceptions=True)


app = FastAPI(title="AI Trading Platform API", version="0.1.0", lifespan=lifespan)
app.include_router(markets_router)
app.include_router(market_data_router)
app.include_router(market_stream_router)
app.include_router(backtest_router)
app.include_router(ai_router)
app.include_router(options_router)
app.include_router(paper_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness endpoint: the API process is healthy even in degraded mode."""
    return {"status": "ok"}


@app.get("/ready")
def readiness() -> dict[str, str]:
    """Readiness reflects configured market-data, option-chain and execution prerequisites."""
    market_error = getattr(app.state, "market_data_startup_error", None)
    option_error = getattr(app.state, "option_chain_startup_error", None)
    execution_error = getattr(app.state, "execution_startup_error", None)
    return {"status": "ok" if market_error is None and option_error is None and execution_error is None else "degraded"}
