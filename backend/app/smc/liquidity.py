from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from app.market.models import Candle

class LiquidityPool(BaseModel):
    side: str  # BUY_SIDE / SELL_SIDE
    price: Decimal
    indices: tuple[int, ...]
    tolerance: Decimal

class LiquiditySweep(BaseModel):
    side: str
    pool_price: Decimal
    timestamp: datetime
    candle_index: int

def detect_liquidity(candles: list[Candle], tolerance: Decimal = Decimal("0.001")) -> tuple[list[LiquidityPool], list[LiquiditySweep]]:
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    pools: list[LiquidityPool] = []
    for i in range(len(candles)):
        for j in range(i + 1, len(candles)):
            for side, a, b in (("BUY_SIDE", candles[i].high, candles[j].high), ("SELL_SIDE", candles[i].low, candles[j].low)):
                base = max(abs(a), abs(b), Decimal("1"))
                if abs(a - b) / base <= tolerance:
                    price = (a + b) / Decimal("2")
                    pools.append(LiquidityPool(side=side, price=price, indices=(i, j), tolerance=tolerance))
    # De-duplicate overlapping equal-level pools deterministically.
    unique: dict[tuple[str, str, tuple[int, ...]], LiquidityPool] = {}
    for p in pools:
        key = (p.side, str(p.price), p.indices)
        unique[key] = p
    pools = list(unique.values())
    sweeps: list[LiquiditySweep] = []
    for p in pools:
        start = p.indices[-1] + 1
        for i in range(start, len(candles)):
            c = candles[i]
            if p.side == "BUY_SIDE" and c.high > p.price and c.close < p.price:
                sweeps.append(LiquiditySweep(side=p.side, pool_price=p.price, timestamp=c.timestamp, candle_index=i))
                break
            if p.side == "SELL_SIDE" and c.low < p.price and c.close > p.price:
                sweeps.append(LiquiditySweep(side=p.side, pool_price=p.price, timestamp=c.timestamp, candle_index=i))
                break
    return pools, sweeps
