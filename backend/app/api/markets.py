"""Market-data API endpoints."""

from fastapi import APIRouter

from app.market.models import Timeframe

router = APIRouter(prefix="/api/v1/markets", tags=["markets"])


@router.get("/timeframes")
def supported_timeframes() -> dict[str, list[str]]:
    """Return the canonical timeframes defined by the platform blueprint."""
    return {"timeframes": [timeframe.value for timeframe in Timeframe]}
