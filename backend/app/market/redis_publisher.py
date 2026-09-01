"""Redis live-market publisher boundary."""

import json
from dataclasses import asdict, is_dataclass
from typing import Any


class RedisMarketPublisher:
    def __init__(self, redis_client: Any, channel: str = "market.events") -> None:
        self.redis = redis_client
        self.channel = channel

    async def publish(self, event: Any) -> None:
        if is_dataclass(event):
            payload = asdict(event)
        elif hasattr(event, "model_dump"):
            payload = event.model_dump(mode="json")
        else:
            raise TypeError("market event must be dataclass or pydantic model")
        await self.redis.publish(self.channel, json.dumps(payload, default=str))
