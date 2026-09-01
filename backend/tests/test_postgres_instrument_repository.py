from datetime import datetime, timezone
from decimal import Decimal

from app.market.models import Instrument, InstrumentType
from app.market.postgres_repository import PostgresInstrumentRepository


class FakeDb:
    def __init__(self) -> None:
        self.rows = {}
        self.last_query = ""
        self.last_params = {}

    def fetch_one(self, query, params):
        self.last_query, self.last_params = query, params
        return self.rows.get(params["instrument_id"])

    def fetch_all(self, query, params):
        self.last_query, self.last_params = query, params
        return list(self.rows.values())

    def execute(self, query, params):
        self.last_query, self.last_params = query, params
        self.rows[params["id"]] = params.copy()


def test_postgres_repository_upsert_get_and_list() -> None:
    db = FakeDb()
    repo = PostgresInstrumentRepository(db)
    instrument = Instrument(
        id="nifty-front",
        symbol="NIFTY",
        exchange="NSE",
        market="equity_derivatives",
        instrument_type=InstrumentType.FUTURE,
        expiry=datetime(2026, 9, 24, tzinfo=timezone.utc),
        strike=Decimal("25000"),
        lot_size=75,
        tick_size=Decimal("0.05"),
    )

    assert repo.upsert(instrument) == instrument
    assert repo.get("nifty-front") == instrument
    assert repo.list_active() == [instrument]
    assert "ON CONFLICT" in db.last_query or "active = TRUE" in db.last_query
