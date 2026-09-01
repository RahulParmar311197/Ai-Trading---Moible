"""Persistence boundary for canonical market ticks."""

from collections.abc import Mapping
from typing import Any, Protocol


class TickSqlExecutor(Protocol):
    def fetch_all(self, query: str, params: Mapping[str, Any]) -> list[Mapping[str, Any]]: ...
    def execute(self, query: str, params: Mapping[str, Any]) -> None: ...


UPSERT_TICK = """
INSERT INTO market_ticks
(id, instrument_id, timestamp, price, volume, bid, ask)
VALUES (:id, :instrument_id, :timestamp, :price, :volume, :bid, :ask)
ON CONFLICT (id) DO UPDATE SET
price=EXCLUDED.price, volume=EXCLUDED.volume,
bid=EXCLUDED.bid, ask=EXCLUDED.ask
"""

SELECT_TICKS = """
SELECT id, instrument_id, timestamp, price, volume, bid, ask
FROM market_ticks
WHERE instrument_id = :instrument_id
  AND timestamp >= :start_time
  AND timestamp < :end_time
ORDER BY timestamp ASC, id ASC
"""


class PostgresTickRepository:
    def __init__(self, db: TickSqlExecutor) -> None:
        self.db = db

    def upsert(self, tick: Mapping[str, Any]) -> None:
        self.db.execute(UPSERT_TICK, dict(tick))

    def list_range(
        self,
        instrument_id: str,
        start_time: Any,
        end_time: Any,
    ) -> list[Mapping[str, Any]]:
        return self.db.fetch_all(
            SELECT_TICKS,
            {
                "instrument_id": instrument_id,
                "start_time": start_time,
                "end_time": end_time,
            },
        )
