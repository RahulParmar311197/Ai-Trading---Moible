"""SQLAlchemy engine and repository-facing SQL executor."""

from collections.abc import Mapping
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.config import settings


def create_database_engine(database_url: str | None = None) -> Engine:
    """Create the PostgreSQL engine without opening a connection at import time."""
    return create_engine(database_url or settings.database_url, pool_pre_ping=True)


class SQLAlchemyExecutor:
    """Adapt SQLAlchemy connections to the repository SqlExecutor contract."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def fetch_one(self, query: str, params: Mapping[str, Any]) -> Mapping[str, Any] | None:
        with self.engine.connect() as connection:
            row = connection.execute(text(query), dict(params)).mappings().first()
            return None if row is None else dict(row)

    def fetch_all(self, query: str, params: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        with self.engine.connect() as connection:
            rows = connection.execute(text(query), dict(params)).mappings().all()
            return [dict(row) for row in rows]

    def execute(self, query: str, params: Mapping[str, Any]) -> None:
        with self.engine.begin() as connection:
            connection.execute(text(query), dict(params))
