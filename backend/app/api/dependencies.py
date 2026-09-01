"""FastAPI dependencies for persistence boundaries."""

from functools import lru_cache

from app.config import settings
from app.database.session import SQLAlchemyExecutor, create_database_engine
from app.market.candle_repository import PostgresCandleRepository
from app.backtest.repository import PostgresBacktestRepository


@lru_cache(maxsize=1)
def get_candle_repository() -> PostgresCandleRepository:
    engine = create_database_engine(settings.database_url)
    return PostgresCandleRepository(SQLAlchemyExecutor(engine))


@lru_cache(maxsize=1)
def get_backtest_repository() -> PostgresBacktestRepository:
    engine = create_database_engine(settings.database_url)
    return PostgresBacktestRepository(SQLAlchemyExecutor(engine))
