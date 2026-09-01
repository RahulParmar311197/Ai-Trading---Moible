from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from app.market.models import Candle, Timeframe
from .models import Direction

class FairValueGap(BaseModel):
    direction: Direction
    top: Decimal
    bottom: Decimal
    timeframe: Timeframe
    created_at: datetime
    candle_index: int
    mitigated: bool = False
    filled_percentage: Decimal = Decimal("0")
    invalidated: bool = False

def detect_fair_value_gaps(candles: list[Candle], minimum_size: Decimal = Decimal("0")) -> list[FairValueGap]:
    if minimum_size < 0:
        raise ValueError("minimum_size must be non-negative")
    result: list[FairValueGap] = []
    for i in range(2, len(candles)):
        a, _, c = candles[i - 2], candles[i - 1], candles[i]
        if c.low - a.high >= minimum_size and c.low > a.high:
            result.append(FairValueGap(direction=Direction.BULLISH, top=c.low, bottom=a.high, timeframe=c.timeframe, created_at=c.timestamp, candle_index=i))
        if a.low - c.high >= minimum_size and a.low > c.high:
            result.append(FairValueGap(direction=Direction.BEARISH, top=a.low, bottom=c.high, timeframe=c.timeframe, created_at=c.timestamp, candle_index=i))
    return result
