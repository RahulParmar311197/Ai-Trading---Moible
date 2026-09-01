"""Redis-backed live market state boundary.

The service stores the latest normalized market event per instrument and keeps
provider-specific transport details out of the state layer.
"""

from collections.abc import Mapping
from typing import Any, Protocol

from app.market.models import MarketEvent


class RedisClient(Protocol):
    def set(self, key: str, value: str) -> Any: ...
    def get(self, key: str) -> Any: ...


class RedisMarketState:
    PREFIX = "market:latest:"

    def __init__(self, client: RedisClient) -> None:
        self.client = client

    def key(self, instrument_id: str) -> str:
        return f"{self.PREFIX}{instrument_id}"

    def publish_latest(self, event: MarketEvent) -> None:
        self.client.set(self.key(event.instrument_id), event.model_dump_json())

    def get_latest(self, instrument_id: str) -> Mapping[str, Any] | None:
        payload = self.client.get(self.key(instrument_id))
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return MarketEvent.model_validate_json(payload).model_dump()
