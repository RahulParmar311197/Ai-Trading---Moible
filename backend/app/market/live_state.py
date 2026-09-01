"""Live market-event fan-out and Redis state integration."""

from collections.abc import Awaitable, Callable

from app.market.models import MarketEvent
from app.market.redis_state import RedisMarketState


class LiveMarketPublisher:
    """Persist the latest event and fan it out to connected WebSocket clients."""

    def __init__(
        self,
        redis_state: RedisMarketState,
        fanout: Callable[[MarketEvent], Awaitable[None]],
    ) -> None:
        self.redis_state = redis_state
        self.fanout = fanout

    async def publish(self, event: MarketEvent) -> None:
        self.redis_state.publish_latest(event)
        await self.fanout(event)
