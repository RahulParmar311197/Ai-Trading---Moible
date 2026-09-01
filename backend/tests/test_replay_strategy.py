from datetime import datetime, timezone
from decimal import Decimal

from app.backtest.engine import MarketOrder, Side
from app.market.models import Candle, Timeframe
from app.replay.engine import ReplayEngine


def candle(i: int) -> Candle:
    return Candle(
        instrument_id="NIFTY",
        timestamp=datetime(2026, 1, 1, 9, 15 + i, tzinfo=timezone.utc),
        timeframe=Timeframe.M1,
        open=Decimal("100") + i,
        high=Decimal("105") + i,
        low=Decimal("95") + i,
        close=Decimal("100") + i,
        volume=Decimal("100"),
    )


class VisibleOnlyStrategy:
    def __init__(self):
        self.visible_counts = []

    def on_candle(self, candles):
        self.visible_counts.append(len(candles))
        if len(candles) == 2:
            return MarketOrder(Side.LONG, Decimal("1"), candles[-1].close, Decimal("95"), Decimal("110"))
        return None


def test_replay_strategy_receives_only_visible_candles():
    strategy = VisibleOnlyStrategy()
    signals = ReplayEngine([candle(0), candle(1), candle(2)]).run_strategy(strategy)

    assert strategy.visible_counts == [1, 2, 3]
    assert len(signals) == 1
    assert signals[0].sequence == 1
    assert signals[0].timestamp == candle(1).timestamp


def test_replay_strategy_evaluation_is_deterministic_after_reset():
    engine = ReplayEngine([candle(0), candle(1), candle(2)])
    first = engine.run_strategy(VisibleOnlyStrategy())
    second = engine.run_strategy(VisibleOnlyStrategy())

    assert [(s.sequence, s.order.entry_price) for s in first] == [(s.sequence, s.order.entry_price) for s in second]
