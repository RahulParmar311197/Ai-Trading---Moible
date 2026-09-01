from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from app.market.models import Candle

class SwingPoint(BaseModel):
    index: int
    timestamp: datetime
    price: Decimal
    kind: str  # HIGH / LOW
    strength: int

def detect_swings(candles: list[Candle], length: int = 3) -> list[SwingPoint]:
    """Return confirmed pivots; a pivot is emitted only after `length` bars to its right."""
    if length < 1:
        raise ValueError("length must be >= 1")
    result: list[SwingPoint] = []
    for i in range(length, len(candles) - length):
        c = candles[i]
        left_right = candles[i-length:i] + candles[i+1:i+length+1]
        if c.high > max(x.high for x in left_right):
            result.append(SwingPoint(index=i, timestamp=c.timestamp, price=c.high, kind="HIGH", strength=length))
        if c.low < min(x.low for x in left_right):
            result.append(SwingPoint(index=i, timestamp=c.timestamp, price=c.low, kind="LOW", strength=length))
    return result
