from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from app.market.models import Candle
from .models import Direction
from .swings import SwingPoint

class StructureEvent(BaseModel):
    kind: str  # BOS / MSS / CHOCH
    direction: Direction
    timestamp: datetime
    level: Decimal
    swing_index: int

def detect_structure(candles: list[Candle], swings: list[SwingPoint], close_break: bool = True) -> list[StructureEvent]:
    """Detect first confirmed break of each prior swing, without repeated events."""
    events: list[StructureEvent] = []
    highs = [s for s in swings if s.kind == "HIGH"]
    lows = [s for s in swings if s.kind == "LOW"]
    broken_highs: set[int] = set()
    broken_lows: set[int] = set()
    last_direction: Direction | None = None
    for i, candle in enumerate(candles):
        prior_highs = [s for s in highs if s.index < i and s.index not in broken_highs]
        prior_lows = [s for s in lows if s.index < i and s.index not in broken_lows]
        price_high = candle.close if close_break else candle.high
        price_low = candle.close if close_break else candle.low
        if prior_highs and price_high > prior_highs[-1].price:
            s = prior_highs[-1]
            kind = "BOS" if last_direction in (None, Direction.BULLISH) else "CHOCH"
            if kind == "CHOCH":
                kind = "MSS"
            events.append(StructureEvent(kind=kind, direction=Direction.BULLISH, timestamp=candle.timestamp, level=s.price, swing_index=s.index))
            broken_highs.add(s.index)
            last_direction = Direction.BULLISH
        if prior_lows and price_low < prior_lows[-1].price:
            s = prior_lows[-1]
            kind = "BOS" if last_direction in (None, Direction.BEARISH) else "CHOCH"
            if kind == "CHOCH":
                kind = "MSS"
            events.append(StructureEvent(kind=kind, direction=Direction.BEARISH, timestamp=candle.timestamp, level=s.price, swing_index=s.index))
            broken_lows.add(s.index)
            last_direction = Direction.BEARISH
    return events
