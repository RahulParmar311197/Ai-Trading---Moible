"""REST market-data endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_candle_repository
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
    repository: PostgresCandleRepository = Depends(get_candle_repository),
) -> dict[str, object]:
    if start_time is None or end_time is None:
        raise HTTPException(status_code=400, detail="start_time and end_time are required")
    if start_time >= end_time:
        raise HTTPException(status_code=400, detail="start_time must be before end_time")

    candles = repository.list_range(instrument_id, timeframe.value, start_time, end_time)
    return {"instrument_id": instrument_id, "timeframe": timeframe.value, "candles": candles}
