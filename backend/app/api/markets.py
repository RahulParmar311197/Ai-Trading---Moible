"""Market-data API endpoints."""

from fastapi import APIRouter

from app.market.models import Timeframe

router = APIRouter(prefix="/api/v1/markets", tags=["markets"])


@router.get("/timeframes")
def supported_timeframes() -> dict[str, list[str]]:
    """Return candle intervals supported by the public timeframe API.

    ``Timeframe.TICK`` is an internal event interval used by live-feed
    normalization and is intentionally excluded from candle aggregation
    timeframes exposed to clients.
    """
    return {
        "timeframes": [
            timeframe.value for timeframe in Timeframe if timeframe is not Timeframe.TICK
        ]
    }
