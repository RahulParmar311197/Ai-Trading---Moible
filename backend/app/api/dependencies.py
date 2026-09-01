"""FastAPI dependencies for market-data persistence."""

from functools import lru_cache

from app.config import settings
from app.database.session import SQLAlchemyExecutor, create_database_engine
from app.market.candle_repository import PostgresCandleRepository


@lru_cache(maxsize=1)
def get_candle_repository() -> PostgresCandleRepository:
    engine = create_database_engine(settings.database_url)
    return PostgresCandleRepository(SQLAlchemyExecutor(engine))
