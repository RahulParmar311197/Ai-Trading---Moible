from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from pydantic import BaseModel, Field

from app.market.models import Candle

class Direction(StrEnum):
    BULLISH = "bullish"
    BEARISH = "bearish"

class Bias(StrEnum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"

class MarketStructureEvent(BaseModel):
    kind: str
    direction: Direction
    timestamp: datetime
    level: Decimal
    broken_swing_timestamp: datetime | None = None

class SignalContext(BaseModel):
    bias: Bias = Bias.NEUTRAL
    bos: bool = False
    mss: bool = False
    choch: bool = False
    liquidity_sweep: bool = False
    fvg: bool = False
    order_block: bool = False
    score: int = Field(default=0, ge=0, le=100)
    reasons: tuple[str, ...] = ()

CandleList = list[Candle]
