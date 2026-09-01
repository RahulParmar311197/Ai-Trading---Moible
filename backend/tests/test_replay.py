from datetime import datetime, timezone
from decimal import Decimal

from app.market.models import Candle, Timeframe
from app.replay import ReplayEngine, ReplaySpeed


def candle(ts: int, close: str) -> Candle:
    value = Decimal(close)
    return Candle(
        instrument_id="NIFTY",
        timestamp=datetime.fromtimestamp(ts, tz=timezone.utc),
        timeframe=Timeframe.M1,
        open=value - 1,
        high=value + 1,
        low=value - 2,
        close=value,
        volume=Decimal("10"),
    )


def test_replay_orders_deterministically_and_exposes_only_history():
    engine = ReplayEngine([candle(120, "102"), candle(60, "101"), candle(60, "100")])
    seen = []
    engine.on_event(lambda state: seen.append((state.current_index, len(state.candles))))

    engine.run()

    assert [e.candle.close for e in engine.events] == [Decimal("101"), Decimal("100"), Decimal("102")]
    assert seen == [(0, 1), (1, 2), (2, 3)]
    assert engine.state.current_timestamp == engine.events[-1].candle.timestamp


def test_replay_timeframe_filter_and_step_controls():
    candles = [candle(60, "101"), candle(120, "102")]
    other = candle(180, "103").model_copy(update={"timeframe": Timeframe.H1})
    engine = ReplayEngine(candles + [other], timeframe=Timeframe.M1, speed=ReplaySpeed.X5)

    assert len(engine.events) == 2
    assert engine.clock.speed == ReplaySpeed.X5
    assert engine.step().current_index == 0
    assert engine.step_previous().current_index == -1
    assert engine.state.candles == ()


def test_replay_reset_restores_initial_state_and_statistics():
    engine = ReplayEngine([candle(60, "101")], starting_balance=Decimal("100000"))
    engine.step()
    engine.statistics.record_trade(Decimal("50"), Decimal("1"))

    engine.reset()

    assert engine.clock.index == -1
    assert engine.statistics.ending_balance == Decimal("100000")
    assert engine.statistics.trades == 0
    assert engine.statistics.net_pnl == 0


def test_replay_statistics_are_deterministic():
    engine = ReplayEngine([], starting_balance=Decimal("1000"))
    engine.statistics.record_trade(Decimal("100"), Decimal("2"))
    engine.statistics.record_trade(Decimal("-50"), Decimal("-1"))

    assert engine.statistics.ending_balance == Decimal("1050")
    assert engine.statistics.net_pnl == Decimal("50")
    assert engine.statistics.win_rate == Decimal("50")
    assert engine.statistics.average_r == Decimal("0.5")
