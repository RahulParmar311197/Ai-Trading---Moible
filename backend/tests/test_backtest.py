from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.backtest.engine import BacktestEngine, BacktestReport, MarketOrder, Side
from app.market.models import Candle, Timeframe


def candle(ts: int, low: str = "99", high: str = "101", close: str = "100") -> Candle:
    return Candle(instrument_id="TEST", timestamp=datetime.fromtimestamp(ts, timezone.utc), timeframe=Timeframe.M1,
                  open=Decimal("100"), high=Decimal(high), low=Decimal(low), close=Decimal(close), volume=Decimal("1"))


class OneShot:
    def __init__(self, order):
        self.order = order
        self.seen = []

    def on_candle(self, candles):
        self.seen.append(len(candles))
        if len(self.seen) == 1:
            return self.order
        return None


def test_backtest_is_deterministic_and_does_not_expose_future_candles():
    strategy = OneShot(MarketOrder(Side.LONG, Decimal("10"), Decimal("100")))
    result = BacktestEngine([candle(60, close="100"), candle(0, close="100")], starting_balance=Decimal("1000")).run(strategy)
    assert strategy.seen == [1, 2]
    assert result.ending_balance == Decimal("1000")
    assert result.net_pnl == Decimal("0")


def test_target_and_stop_are_resolved_from_current_candle_only():
    target = OneShot(MarketOrder(Side.LONG, Decimal("1"), Decimal("100"), target_price=Decimal("101")))
    result = BacktestEngine([candle(0, high="102", close="100")]).run(target)
    assert result.trades[0].exit_price == Decimal("101")
    assert result.net_pnl == Decimal("1")


def test_position_can_remain_open_until_a_later_candle_hits_target():
    strategy = OneShot(MarketOrder(Side.LONG, Decimal("1"), Decimal("100"), target_price=Decimal("103")))
    result = BacktestEngine([candle(0, high="101"), candle(60, high="104")]).run(strategy)
    assert len(result.trades) == 1
    assert result.trades[0].exit_price == Decimal("103")
    assert [event.event for event in result.order_events] == ["OPEN", "CLOSE"]


def test_open_position_is_closed_at_end_of_data():
    strategy = OneShot(MarketOrder(Side.LONG, Decimal("1"), Decimal("100")))
    result = BacktestEngine([candle(0), candle(60, close="102")]).run(strategy)
    assert result.trades[0].exit_price == Decimal("102")
    assert result.order_events[-1].event == "CLOSE_END"


def test_fees_and_slippage_are_applied_deterministically():
    strategy = OneShot(MarketOrder(Side.LONG, Decimal("2"), Decimal("100"), target_price=Decimal("101")))
    result = BacktestEngine([candle(0, high="102", close="100")], fee_rate=Decimal("0.01"), slippage_bps=Decimal("10")).run(strategy)
    assert result.trades[0].fees > 0
    assert result.trades[0].slippage > 0
    assert result.net_pnl < Decimal("2")


def test_invalid_order_is_rejected():
    strategy = OneShot(MarketOrder(Side.LONG, Decimal("0"), Decimal("100")))
    with pytest.raises(ValueError, match="quantity"):
        BacktestEngine([candle(0)]).run(strategy)


def test_drawdown_win_rate_and_expectancy_are_reported():
    assert BacktestEngine([candle(0)]).run(OneShot(None)).max_drawdown == Decimal("0")
    result = BacktestEngine([candle(0, high="101", close="101")]).run(
        OneShot(MarketOrder(Side.LONG, Decimal("1"), Decimal("100"))))
    assert result.win_rate == Decimal("100")
    assert result.expectancy == Decimal("1")


def test_out_of_sample_split_is_chronological_and_non_overlapping():
    engine = BacktestEngine([candle(0), candle(60), candle(120), candle(180)])
    train, test = engine.out_of_sample_split(Decimal("0.5"))
    assert len(train.candles) == 2
    assert len(test.candles) == 2
    assert train.candles[-1].timestamp < test.candles[0].timestamp


def test_out_of_sample_ratio_must_leave_both_sides_non_empty():
    engine = BacktestEngine([candle(0), candle(60)])
    with pytest.raises(ValueError):
        engine.out_of_sample_split(Decimal("0"))
    with pytest.raises(ValueError):
        engine.out_of_sample_split(Decimal("1"))


def test_risk_based_sizing_uses_balance_and_stop_distance():
    strategy = OneShot(MarketOrder(Side.LONG, None, Decimal("100"), stop_price=Decimal("95"), target_price=Decimal("110")))
    result = BacktestEngine([candle(0, low="99", high="101")], starting_balance=Decimal("1000"),
                            risk_per_trade=Decimal("1")).run(strategy)
    assert result.trades[0].quantity == Decimal("2")
    assert result.order_events[0].quantity == Decimal("2")


def test_risk_based_sizing_requires_stop_and_valid_risk_percent():
    with pytest.raises(ValueError, match="risk_per_trade"):
        BacktestEngine([candle(0)], risk_per_trade=Decimal("0"))
    with pytest.raises(ValueError, match="stop price"):
        BacktestEngine([candle(0)], risk_per_trade=Decimal("1")).run(
            OneShot(MarketOrder(Side.LONG, None, Decimal("100"))))


def test_explicit_quantity_remains_authoritative_when_risk_sizing_enabled():
    strategy = OneShot(MarketOrder(Side.LONG, Decimal("3"), Decimal("100"), stop_price=Decimal("95")))
    result = BacktestEngine([candle(0)], starting_balance=Decimal("1000"), risk_per_trade=Decimal("1")).run(strategy)
    assert result.trades[0].quantity == Decimal("3")


def test_backtest_report_is_a_stable_projection_of_result():
    result = BacktestEngine([candle(0, high="101", close="101")]).run(
        OneShot(MarketOrder(Side.LONG, Decimal("1"), Decimal("100"))))
    report = BacktestReport.from_result(result)
    assert report.trade_count == 1
    assert report.net_pnl == result.net_pnl
    assert report.trades == tuple(result.trades)
    assert report.order_events == tuple(result.order_events)
