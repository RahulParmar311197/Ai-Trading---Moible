from dataclasses import dataclass

import pytest

from app.market.redis_publisher import RedisMarketPublisher


@dataclass
class Event:
    instrument_id: str
    close: str


class FakeRedis:
    def __init__(self):
        self.calls = []

    async def publish(self, channel, payload):
        self.calls.append((channel, payload))


@pytest.mark.asyncio
async def test_publish_canonical_event():
    redis = FakeRedis()
    publisher = RedisMarketPublisher(redis)
    await publisher.publish(Event("NIFTY", "25000"))
    assert redis.calls[0][0] == "market.events"
    assert '"instrument_id": "NIFTY"' in redis.calls[0][1]
