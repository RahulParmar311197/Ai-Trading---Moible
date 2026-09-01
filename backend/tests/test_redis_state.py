from datetime import datetime, timezone
from decimal import Decimal

from app.market.models import MarketEvent, Timeframe
from app.market.redis_state import RedisMarketState


class FakeRedis:
    def __init__(self) -> None:
        self.values = {}

    def set(self, key, value):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)


def test_redis_market_state_round_trip() -> None:
    client = FakeRedis()
    state = RedisMarketState(client)
    event = MarketEvent(
        instrument_id="nifty-front",
        timestamp=datetime(2026, 9, 1, 9, 15, tzinfo=timezone.utc),
        timeframe=Timeframe.M15,
        open=Decimal("25000"), high=Decimal("25050"),
        low=Decimal("24980"), close=Decimal("25030"), volume=Decimal("100"),
    )
    state.publish_latest(event)
    latest = state.get_latest("nifty-front")
    assert latest is not None
    assert latest["instrument_id"] == "nifty-front"
    assert latest["close"] == Decimal("25030")


def test_redis_market_state_missing_returns_none() -> None:
    assert RedisMarketState(FakeRedis()).get_latest("missing") is None
