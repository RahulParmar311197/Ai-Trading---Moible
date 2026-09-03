from datetime import datetime, timezone
from decimal import Decimal

from app.backtest.engine import BacktestEngine, MarketOrder, Side
from app.market.models import Candle, Timeframe
from app.paper.engine import PaperBroker
from app.replay import ReplayEngine, ReplayPaperSession


def candle(ts: int, *, high: str, close: str) -> Candle:
    return Candle(
        instrument_id="TEST",
        timestamp=datetime.fromtimestamp(ts, tz=timezone.utc),
        timeframe=Timeframe.M1,
        open=Decimal("100"),
        high=Decimal(high),
        low=Decimal("99"),
        close=Decimal(close),
        volume=Decimal("10"),
    )


class OneShotTargetStrategy:
    def __init__(self) -> None:
        self.seen: list[int] = []

    def on_candle(self, candles):
        self.seen.append(len(candles))
        if len(self.seen) == 1:
            return MarketOrder(
                Side.LONG,
                Decimal("1"),
                Decimal("100"),
                target_price=Decimal("102"),
            )
        return None


def test_analyze_replay_backtest_paper_flow_is_deterministic_and_stays_non_live():
    candles = [
        candle(0, high="101", close="100"),
        candle(60, high="103", close="102"),
    ]

    backtest_strategy = OneShotTargetStrategy()
    backtest = BacktestEngine(candles, starting_balance=Decimal("1000")).run(backtest_strategy)

    replay_strategy = OneShotTargetStrategy()
    paper = PaperBroker(starting_balance=Decimal("1000"))
    replay = ReplayEngine(candles)
    session = ReplayPaperSession(replay, paper, replay_strategy)
    session.run()

    assert backtest_strategy.seen == [1, 2]
    assert replay_strategy.seen == [1, 2]
    assert len(backtest.trades) == 1
    assert backtest.trades[0].entry_price == Decimal("100")
    assert backtest.trades[0].exit_price == Decimal("102")
    assert backtest.net_pnl == Decimal("2")

    assert [execution.order_id for execution in session.executions] == ["replay-00000000"]
    assert len(paper.fills) == 2
    assert paper.fills[0].price == Decimal("100")
    assert paper.fills[1].price == Decimal("102")
    assert paper.positions == {}
    assert paper.balance == Decimal("1002")
    assert paper.realized_pnl_total == Decimal("2")

    # The replay-to-paper boundary accepts only PaperBroker, so this path cannot
    # submit an Upstox/Dhan/live order. Live execution remains a separate gate.
    assert all(fill.order_id.startswith("replay-00000000") for fill in paper.fills)
