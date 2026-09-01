"""PostgreSQL repository for canonical instruments."""

from collections.abc import Mapping
from typing import Any, Protocol

from .models import Instrument
from .repository import InstrumentRepository
from .sql import instrument_to_params


class SqlExecutor(Protocol):
    """Minimal DB contract; keeps domain code independent of a DB driver."""

    def fetch_one(self, query: str, params: Mapping[str, Any]) -> Mapping[str, Any] | None: ...
    def fetch_all(self, query: str, params: Mapping[str, Any]) -> list[Mapping[str, Any]]: ...
    def execute(self, query: str, params: Mapping[str, Any]) -> None: ...


UPSERT_INSTRUMENT = """
INSERT INTO instruments (
 id, symbol, exchange, market, instrument_type, underlying, expiry,
 strike, option_type, lot_size, tick_size, currency, active, updated_at
) VALUES (
 :id, :symbol, :exchange, :market, :instrument_type, :underlying, :expiry,
 :strike, :option_type, :lot_size, :tick_size, :currency, :active, NOW()
)
ON CONFLICT (id) DO UPDATE SET
 symbol=EXCLUDED.symbol, exchange=EXCLUDED.exchange, market=EXCLUDED.market,
 instrument_type=EXCLUDED.instrument_type, underlying=EXCLUDED.underlying,
 expiry=EXCLUDED.expiry, strike=EXCLUDED.strike, option_type=EXCLUDED.option_type,
 lot_size=EXCLUDED.lot_size, tick_size=EXCLUDED.tick_size,
 currency=EXCLUDED.currency, active=EXCLUDED.active, updated_at=NOW()
"""

GET_INSTRUMENT = "SELECT * FROM instruments WHERE id = :instrument_id"
LIST_ACTIVE = "SELECT * FROM instruments WHERE active = TRUE ORDER BY symbol, exchange, id"


def _to_instrument(row: Mapping[str, Any]) -> Instrument:
    return Instrument.model_validate(dict(row))


class PostgresInstrumentRepository(InstrumentRepository):
    def __init__(self, db: SqlExecutor) -> None:
        self.db = db

    def get(self, instrument_id: str) -> Instrument | None:
        row = self.db.fetch_one(GET_INSTRUMENT, {"instrument_id": instrument_id})
        return None if row is None else _to_instrument(row)

    def upsert(self, instrument: Instrument) -> Instrument:
        self.db.execute(UPSERT_INSTRUMENT, instrument_to_params(instrument))
        return instrument

    def list_active(self) -> list[Instrument]:
        return [_to_instrument(row) for row in self.db.fetch_all(LIST_ACTIVE, {})]
