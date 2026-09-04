import asyncio
import json
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.api.market_stream import MarketEventHub, consume_redis_events
from app.market.models import MarketEvent, Timeframe


class FakePubSub:
    def __init__(self, messages):
        self.messages = messages
        self.subscribed = None
        self.unsubscribed = None
        self.closed = False

    async def subscribe(self, channel):
        self.subscribed = channel

    async def listen(self):
        for message in self.messages:
            yield message

    async def unsubscribe(self, channel):
        self.unsubscribed = channel

    async def close(self):
        self.closed = True


class FakeRedis:
    def __init__(self, messages):
        self.pubsub_instance = FakePubSub(messages)

    def pubsub(self):
        return self.pubsub_instance


def event_payload(instrument_id: str) -> str:
    return MarketEvent(
        instrument_id=instrument_id,
        timestamp=datetime(2026, 9, 1, 9, 15, tzinfo=timezone.utc),
        timeframe=Timeframe.M15,
        open=Decimal("25000"),
        high=Decimal("25050"),
        low=Decimal("24980"),
        close=Decimal("25030"),
        volume=Decimal("100"),
    ).model_dump_json()


@pytest.mark.asyncio
async def test_redis_events_reach_matching_subscriber(monkeypatch):
    hub = MarketEventHub()
    monkeypatch.setattr("app.api.market_stream.market_event_hub", hub)
    redis = FakeRedis([{"type": "subscribe", "data": 1}, {"type": "message", "data": event_payload("nifty")}])

    stream = hub.subscribe("nifty")
    task = asyncio.create_task(stream.__anext__())
    await asyncio.sleep(0)
    await consume_redis_events(redis)
    payload = await asyncio.wait_for(task, timeout=1)
    assert json.loads(payload)["instrument_id"] == "nifty"
    await stream.aclose()
    assert redis.pubsub_instance.subscribed == "market.events"
    assert redis.pubsub_instance.unsubscribed == "market.events"
    assert redis.pubsub_instance.closed


@pytest.mark.asyncio
async def test_redis_invalid_payload_is_not_broadcast(monkeypatch):
    hub = MarketEventHub()
    monkeypatch.setattr("app.api.market_stream.market_event_hub", hub)
    redis = FakeRedis([{"type": "message", "data": "not-json"}])

    stream = hub.subscribe("nifty")
    task = asyncio.create_task(stream.__anext__())
    await asyncio.sleep(0)
    with pytest.raises(Exception):
        await consume_redis_events(redis)
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    await stream.aclose()
