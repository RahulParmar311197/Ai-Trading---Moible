"""Persistence boundary for canonical market candles."""

from collections.abc import Mapping
from typing import Any, Protocol

from .models import Candle


class CandleSqlExecutor(Protocol):
    def fetch_all(self, query: str, params: Mapping[str, Any]) -> list[Mapping[str, Any]]: ...
    def execute(self, query: str, params: Mapping[str, Any]) -> None: ...


UPSERT_CANDLE = """
INSERT INTO market_candles
(instrument_id, timestamp, timeframe, open, high, low, close, volume)
VALUES (:instrument_id, :timestamp, :timeframe, :open, :high, :low, :close, :volume)
ON CONFLICT (instrument_id, timeframe, timestamp) DO UPDATE SET
open=EXCLUDED.open, high=EXCLUDED.high, low=EXCLUDED.low,
close=EXCLUDED.close, volume=EXCLUDED.volume
"""

SELECT_CANDLES = """
SELECT instrument_id, timestamp, timeframe, open, high, low, close, volume
FROM market_candles
WHERE instrument_id = :instrument_id
  AND timeframe = :timeframe
  AND timestamp >= :start_time
  AND timestamp < :end_time
ORDER BY timestamp ASC
"""


def _to_candle(row: Mapping[str, Any]) -> Candle:
    return Candle.model_validate(dict(row)).validate_ohlc()


class PostgresCandleRepository:
    def __init__(self, db: CandleSqlExecutor) -> None:
        self.db = db

    def upsert(self, candle: Candle) -> Candle:
        self.db.execute(UPSERT_CANDLE, candle.model_dump())
        return candle

    def list_range(self, instrument_id: str, timeframe: str, start_time: Any, end_time: Any) -> list[Candle]:
        rows = self.db.fetch_all(
            SELECT_CANDLES,
            {
                "instrument_id": instrument_id,
                "timeframe": timeframe,
                "start_time": start_time,
                "end_time": end_time,
            },
        )
        return [_to_candle(row) for row in rows]
