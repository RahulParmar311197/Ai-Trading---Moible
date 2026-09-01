from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from app.market.models import Candle
from .models import Direction

class OrderBlock(BaseModel):
    direction: Direction
    top: Decimal
    bottom: Decimal
    created_at: datetime
    candle_index: int
    strength: Decimal

def detect_order_blocks(candles: list[Candle], displacement_factor: Decimal = Decimal("1.5"), lookback: int = 20) -> list[OrderBlock]:
    if displacement_factor <= 0 or lookback < 1:
        raise ValueError("displacement_factor must be > 0 and lookback >= 1")
    result: list[OrderBlock] = []
    for i in range(1, len(candles)):
        c, prev = candles[i], candles[i - 1]
        start = max(0, i - lookback)
        ranges = [x.high - x.low for x in candles[start:i] if x.high >= x.low]
        if not ranges:
            continue
        avg = sum(ranges, Decimal("0")) / Decimal(len(ranges))
        displacement = c.high - c.low
        if displacement < avg * displacement_factor:
            continue
        if c.close > c.open and prev.close < prev.open:
            result.append(OrderBlock(direction=Direction.BULLISH, top=prev.high, bottom=prev.low, created_at=prev.timestamp, candle_index=i-1, strength=min(Decimal("1"), displacement / (avg * displacement_factor))))
        elif c.close < c.open and prev.close > prev.open:
            result.append(OrderBlock(direction=Direction.BEARISH, top=prev.high, bottom=prev.low, created_at=prev.timestamp, candle_index=i-1, strength=min(Decimal("1"), displacement / (avg * displacement_factor))))
    return result
