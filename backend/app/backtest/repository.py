"""Persistence boundary for deterministic backtest reports."""

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any
from uuid import UUID

from app.backtest.engine import BacktestReport


class BacktestSqlExecutor:
    def fetch_one(self, query: str, params: Mapping[str, Any]) -> Mapping[str, Any] | None: ...
    def execute(self, query: str, params: Mapping[str, Any]) -> None: ...


INSERT_BACKTEST = """
INSERT INTO backtests (id, request, report)
VALUES (:id, CAST(:request AS JSONB), CAST(:report AS JSONB))
"""

SELECT_BACKTEST = """
SELECT id, created_at, request, report
FROM backtests
WHERE id = :id
"""


class PostgresBacktestRepository:
    def __init__(self, db: BacktestSqlExecutor) -> None:
        self.db = db

    def save(self, backtest_id: UUID, request: dict[str, Any], report: BacktestReport) -> None:
        import json

        self.db.execute(
            INSERT_BACKTEST,
            {
                "id": str(backtest_id),
                "request": json.dumps(request, sort_keys=True, separators=(",", ":")),
                "report": json.dumps(asdict(report), default=str, sort_keys=True, separators=(",", ":")),
            },
        )

    def get(self, backtest_id: UUID) -> Mapping[str, Any] | None:
        return self.db.fetch_one(SELECT_BACKTEST, {"id": str(backtest_id)})
