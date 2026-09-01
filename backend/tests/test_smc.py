from datetime import datetime, timedelta, timezone
from decimal import Decimal
from app.market.models import Candle, Timeframe


def candle(i: int, o: str, h: str, l: str, c: str) -> Candle:
    return Candle(instrument_id="NIFTY", timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=i), timeframe=Timeframe.M1, open=Decimal(o), high=Decimal(h), low=Decimal(l), close=Decimal(c), volume=Decimal("100"))


def test_swings_are_confirmed_only_after_right_side_bars():
    from app.smc.swings import detect_swings
    candles = [candle(0,"10","11","9","10"), candle(1,"10","12","9.5","11"), candle(2,"11","15","10","14"), candle(3,"14","13","11","12"), candle(4,"12","12.5","10","11")]
    swings = detect_swings(candles, length=1)
    assert [(s.index, s.kind, s.price) for s in swings] == [(2, "HIGH", Decimal("15"))]


def test_structure_emits_one_break_per_swing():
    from app.smc.structure import detect_structure
    from app.smc.swings import SwingPoint
    swings = [SwingPoint(index=1, timestamp=candle(1,"10","12","9","11").timestamp, price=Decimal("12"), kind="HIGH", strength=1)]
    candles = [candle(0,"10","11","9","10"), candle(1,"10","12","9","11"), candle(2,"11","13","10","13"), candle(3,"13","14","12","13.5")]
    events = detect_structure(candles, swings)
    assert len(events) == 1
    assert events[0].kind == "BOS"


def test_fvg_detection():
    from app.smc.fvg import detect_fair_value_gaps
    candles = [candle(0,"10","11","9","10"), candle(1,"10","13","10","12"), candle(2,"12","15","12","14")]
    fvgs = detect_fair_value_gaps(candles)
    assert len(fvgs) == 1
    assert fvgs[0].direction.value == "bullish"
    assert fvgs[0].bottom == Decimal("11")
    assert fvgs[0].top == Decimal("12")


def test_premium_discount_range_and_zone():
    from app.smc.premium_discount import premium_discount, zone
    candles = [candle(0,"10","20","5","12"), candle(1,"12","18","8","16")]
    r = premium_discount(candles)
    assert r.midpoint == Decimal("12.5")
    assert zone(Decimal("16"), r) == "PREMIUM"
    assert zone(Decimal("10"), r) == "DISCOUNT"


def test_engine_is_deterministic_and_handles_empty_input():
    from app.smc.engine import SmcEngine
    engine = SmcEngine()
    empty = engine.analyze([])
    assert empty.signal.score == 0
    candles = [candle(i, "10", "10.5", "9.5", "10") for i in range(8)]
    assert engine.analyze(candles).model_dump() == engine.analyze(candles).model_dump()
