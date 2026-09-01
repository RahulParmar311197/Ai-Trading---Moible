from datetime import datetime, timezone
from decimal import Decimal

from app.market.candle_repository import PostgresCandleRepository
from app.market.models import Candle, Timeframe


class FakeDb:
    def __init__(self) -> None:
        self.rows = []
        self.last_query = ""

    def execute(self, query, params):
        self.last_query = query
        self.rows = [params]

    def fetch_all(self, query, params):
        self.last_query = query
        return self.rows


def test_candle_repository_upsert_and_range() -> None:
    db = FakeDb()
    repo = PostgresCandleRepository(db)
    candle = Candle(
        instrument_id="nifty-front",
        timestamp=datetime(2026, 9, 1, 9, 15, tzinfo=timezone.utc),
        timeframe=Timeframe.M15,
        open=Decimal("25000"), high=Decimal("25050"),
        low=Decimal("24980"), close=Decimal("25030"),
    )
    repo.upsert(candle)
    result = repo.list_range(
        "nifty-front", Timeframe.M15.value,
        datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc),
        datetime(2026, 9, 1, 9, 30, tzinfo=timezone.utc),
    )
    assert result == [candle]
    assert "ON CONFLICT" in db.last_query or "timestamp >=" in db.last_query
