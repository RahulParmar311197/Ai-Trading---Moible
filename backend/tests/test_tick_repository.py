from datetime import datetime, timezone
from decimal import Decimal

from app.market.tick_repository import PostgresTickRepository


class FakeDb:
    def __init__(self) -> None:
        self.rows = []
        self.last_query = ""

    def execute(self, query, params):
        self.last_query = query
        self.rows = [dict(params)]

    def fetch_all(self, query, params):
        self.last_query = query
        return self.rows


def test_tick_repository_upsert_and_range() -> None:
    db = FakeDb()
    repo = PostgresTickRepository(db)
    tick = {
        "id": "tick-1",
        "instrument_id": "nifty-front",
        "timestamp": datetime(2026, 9, 1, 9, 15, tzinfo=timezone.utc),
        "price": Decimal("25030"),
        "volume": Decimal("10"),
        "bid": Decimal("25029.95"),
        "ask": Decimal("25030.05"),
    }
    repo.upsert(tick)
    result = repo.list_range(
        "nifty-front",
        datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc),
        datetime(2026, 9, 1, 9, 30, tzinfo=timezone.utc),
    )
    assert result == [tick]
    assert "ON CONFLICT" in db.last_query or "timestamp >=" in db.last_query
