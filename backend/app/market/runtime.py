"""Application-level live market publisher wiring."""

from functools import lru_cache

from app.api.market_stream import market_event_hub
from app.market.live_state import LiveMarketPublisher
from app.market.redis_client import get_redis_client
from app.market.redis_state import RedisMarketState


@lru_cache(maxsize=1)
def get_live_market_publisher() -> LiveMarketPublisher:
    state = RedisMarketState(get_redis_client())
    return LiveMarketPublisher(state, market_event_hub.publish)
