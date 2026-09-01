from decimal import Decimal
from pydantic import BaseModel
from app.market.models import Candle
from .models import Bias, Direction

class DealingRange(BaseModel):
    high: Decimal
    low: Decimal
    midpoint: Decimal

def premium_discount(candles: list[Candle]) -> DealingRange:
    if not candles:
        raise ValueError("at least one candle is required")
    high = max(c.high for c in candles)
    low = min(c.low for c in candles)
    return DealingRange(high=high, low=low, midpoint=(high + low) / Decimal("2"))

def zone(price: Decimal, range_: DealingRange) -> str:
    if price > range_.midpoint:
        return "PREMIUM"
    if price < range_.midpoint:
        return "DISCOUNT"
    return "EQUILIBRIUM"

def preferred_zone(direction: Direction) -> str:
    return "DISCOUNT" if direction == Direction.BULLISH else "PREMIUM"
