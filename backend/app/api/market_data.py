"""REST market-data endpoints."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.market.candle_repository import PostgresCandleRepository
from app.market.models import Timeframe

router = APIRouter(prefix="/api/v1/market-data", tags=["market-data"])


@router.get("/timeframes")
def timeframes() -> dict[str, list[str]]:
    return {"timeframes": [item.value for item in Timeframe]}


@router.get("/candles")
def candles(
    instrument_id: str = Query(min_length=1),
    timeframe: Timeframe = Query(...),
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> dict[str, object]:
    """Return the normalized candle query contract.

    Persistence wiring is deliberately not hidden here: until a concrete DB
    dependency is installed, this endpoint returns a clear 503 rather than
    silently returning fabricated market data.
    """
    if start_time is None or end_time is None:
        raise HTTPException(status_code=400, detail="start_time and end_time are required")
    if start_time >= end_time:
        raise HTTPException(status_code=400, detail="start_time must be before end_time")
    raise HTTPException(status_code=503, detail="market-data persistence dependency is not configured")
