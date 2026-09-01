import asyncio
from datetime import datetime, timezone
from decimal import Decimal

from app.market.live_state import LiveMarketPublisher
from app.market.models import MarketEvent, Timeframe
from app.market.redis_state import RedisMarketState


class FakeRedis:
    def __init__(self) -> None:
        self.values = {}

    def set(self, key, value):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)


def test_live_publisher_persists_before_fanout() -> None:
    async def scenario() -> None:
        state = RedisMarketState(FakeRedis())
        seen = []

        async def fanout(event):
            assert state.get_latest(event.instrument_id) is not None
            seen.append(event)

        publisher = LiveMarketPublisher(state, fanout)
        event = MarketEvent(
            instrument_id="nifty-front",
            timestamp=datetime(2026, 9, 1, 9, 15, tzinfo=timezone.utc),
            timeframe=Timeframe.M15,
            open=Decimal("25000"), high=Decimal("25050"),
            low=Decimal("24980"), close=Decimal("25030"), volume=Decimal("100"),
        )
        await publisher.publish(event)
        assert seen == [event]

    asyncio.run(scenario())
