"""Runtime bridge from a provider-neutral feed into live market delivery."""

import asyncio
from collections.abc import Awaitable, Callable

from app.market.feed import MarketDataFeed
from app.market.models import MarketEvent


class ProviderMarketRunner:
    """Consume normalized provider events and hand them to the live publisher."""

    def __init__(
        self,
        feed: MarketDataFeed,
        publish: Callable[[MarketEvent], Awaitable[None]],
    ) -> None:
        self.feed = feed
        self.publish = publish

    async def run(self, instrument_ids: list[str]) -> None:
        async for event in self.feed.stream(instrument_ids=instrument_ids):
            await self.publish(event)

    def start(self, instrument_ids: list[str]) -> asyncio.Task[None]:
        return asyncio.create_task(self.run(instrument_ids))
