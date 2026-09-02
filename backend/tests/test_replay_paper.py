from datetime import datetime, timezone
from decimal import Decimal

from app.backtest.engine import MarketOrder, Side
from app.market.models import Candle, Timeframe
from app.paper import PaperBroker, OrderStatus
from app.replay import ReplayEngine, ReplayPaperSession


def candle(ts: int, close: str, high: str | None = None, low: str | None = None) -> Candle:
    value = Decimal(close)
    return Candle(
        instrument_id="NIFTY",
        timestamp=datetime.fromtimestamp(ts, tz=timezone.utc),
        timeframe=Timeframe.M1,
        open=value,
        high=Decimal(high) if high is not None else value + 1,
        low=Decimal(low) if low is not None else value - 1,
        close=value,
        volume=Decimal("10"),
    )


class OneShotLongStrategy:
    def __init__(self) -> None:
        self.calls = 0

    def on_candle(self, candles):
        self.calls += 1
        if self.calls != 1:
            return None
        return MarketOrder(
            side=Side.LONG,
            quantity=Decimal("2"),
            entry_price=candles[-1].close,
            stop_price=Decimal("95"),
            target_price=Decimal("105"),
        )


def test_replay_paper_executes_only_through_paper_broker_and_closes_bracket() -> None:
    replay = ReplayEngine([
        candle(60, "100"),
        candle(120, "104"),
        candle(180, "105", high="106"),
    ])
    paper = PaperBroker(starting_balance=Decimal("1000"))
    strategy = OneShotLongStrategy()

    session = ReplayPaperSession(replay, paper, strategy)
    session.run()

    assert len(session.executions) == 1
    assert paper.orders["replay-00000000"].status is OrderStatus.FILLED
    assert paper.orders["replay-00000000-exit-00000002"].status is OrderStatus.FILLED
    assert paper.positions == {}
    assert paper.realized_pnl_total == Decimal("10")


def test_replay_paper_rejects_fractional_strategy_quantity() -> None:
    class FractionalStrategy:
        def on_candle(self, candles):
            return MarketOrder(Side.LONG, Decimal("1.5"), candles[-1].close)

    replay = ReplayEngine([candle(60, "100")])
    session = ReplayPaperSession(replay, PaperBroker(), FractionalStrategy())

    try:
        session.run()
    except ValueError as exc:
        assert str(exc) == "replay paper quantity must be a positive whole number"
    else:
        raise AssertionError("fractional replay paper quantity should be rejected")
