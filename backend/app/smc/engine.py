from decimal import Decimal
from pydantic import BaseModel
from app.market.models import Candle
from .fvg import detect_fair_value_gaps
from .liquidity import detect_liquidity
from .models import Bias, SignalContext
from .order_blocks import detect_order_blocks
from .premium_discount import premium_discount, zone
from .structure import detect_structure
from .swings import detect_swings

class SmcAnalysis(BaseModel):
    swings: list
    structure: list
    liquidity_pools: list
    liquidity_sweeps: list
    fvgs: list
    order_blocks: list
    dealing_range: object | None
    current_zone: str | None
    signal: SignalContext

class SmcEngine:
    """Single deterministic orchestration point for Stage 2 SMC analysis."""
    def __init__(self, swing_length: int = 3, liquidity_tolerance: Decimal = Decimal("0.001"), displacement_factor: Decimal = Decimal("1.5")):
        self.swing_length = swing_length
        self.liquidity_tolerance = liquidity_tolerance
        self.displacement_factor = displacement_factor

    def analyze(self, candles: list[Candle]) -> SmcAnalysis:
        if not candles:
            return SmcAnalysis(swings=[], structure=[], liquidity_pools=[], liquidity_sweeps=[], fvgs=[], order_blocks=[], dealing_range=None, current_zone=None, signal=SignalContext())
        swings = detect_swings(candles, self.swing_length)
        structure = detect_structure(candles, swings)
        pools, sweeps = detect_liquidity(candles, self.liquidity_tolerance)
        fvgs = detect_fair_value_gaps(candles)
        blocks = detect_order_blocks(candles, self.displacement_factor)
        dealing = premium_discount(candles)
        current_zone = zone(candles[-1].close, dealing)
        bias = Bias.NEUTRAL
        reasons: list[str] = []
        if structure:
            bias = Bias.BULLISH if structure[-1].direction.value == "bullish" else Bias.BEARISH
            reasons.append(structure[-1].kind)
        if sweeps:
            reasons.append("liquidity_sweep")
        if fvgs:
            reasons.append("fvg")
        if blocks:
            reasons.append("order_block")
        score = min(100, len(reasons) * 20 + (20 if current_zone in ("PREMIUM", "DISCOUNT") else 0))
        signal = SignalContext(bias=bias, bos=any(e.kind == "BOS" for e in structure), mss=any(e.kind == "MSS" for e in structure), choch=any(e.kind == "CHOCH" for e in structure), liquidity_sweep=bool(sweeps), fvg=bool(fvgs), order_block=bool(blocks), score=score, reasons=tuple(reasons))
        return SmcAnalysis(swings=swings, structure=structure, liquidity_pools=pools, liquidity_sweeps=sweeps, fvgs=fvgs, order_blocks=blocks, dealing_range=dealing, current_zone=current_zone, signal=signal)
