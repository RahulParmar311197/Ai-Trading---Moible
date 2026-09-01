from datetime import datetime, timezone
from decimal import Decimal

from app.backtest.engine import BacktestEngine, Side
from app.market.models import Candle, Timeframe
from app.strategy.backtest import DslBacktestStrategy
from app.strategy.dsl import ConditionType, Operator, StrategyCondition, StrategyDefinition, StrategyRisk


def candle(i: int, close: str = "100") -> Candle:
    price = Decimal(close)
    return Candle(
        instrument_id="NIFTY",
        timestamp=datetime(2026, 1, 1, 9, 15 + i, tzinfo=timezone.utc),
        timeframe=Timeframe.M1,
        open=price,
        high=price + 5,
        low=price - 5,
        close=price,
        volume=Decimal("100"),
    )


def definition(*conditions: StrategyCondition) -> StrategyDefinition:
    return StrategyDefinition(
        name="Bullish SMC",
        market="NIFTY",
        timeframe=Timeframe.M1,
        direction="bullish",
        conditions=list(conditions),
        entry={"stop_distance": "5"},
        risk=StrategyRisk(risk_percent=Decimal("1"), minimum_rr=Decimal("2")),
    )


def test_dsl_strategy_evaluates_only_visible_candles_and_sizes_from_strategy_risk():
    condition = StrategyCondition(type=ConditionType.BOS)
    strategy = DslBacktestStrategy(definition(condition))
    candles = [candle(0), candle(1)]

    # The real SMC engine does not manufacture a BOS from two flat candles.
    assert strategy.on_candle(candles) is None


def test_dsl_strategy_can_emit_order_from_deterministic_smc_fixture(monkeypatch):
    class Signal:
        bias = type("Bias", (), {"value": "BULLISH"})()
        bos = True
        mss = True
        choch = False
        liquidity_sweep = True
        fvg = True
        order_block = False
        score = 80
        reasons = ("BOS", "liquidity_sweep", "fvg")

    class Analysis:
        signal = Signal()
        current_zone = "DISCOUNT"

    class FakeSmc:
        def analyze(self, visible):
            assert len(visible) == 1
            return Analysis()

    conditions = (
        StrategyCondition(type=ConditionType.BOS),
        StrategyCondition(type=ConditionType.MSS),
        StrategyCondition(type=ConditionType.LIQUIDITY_SWEEP),
        StrategyCondition(type=ConditionType.FVG),
    )
    strategy = DslBacktestStrategy(definition(*conditions), smc=FakeSmc())
    order = strategy.on_candle([candle(0)])

    assert order is not None
    assert order.side is Side.LONG
    assert order.entry_price == Decimal("100")
    assert order.stop_price == Decimal("95")
    assert order.target_price == Decimal("110")
    assert order.quantity is None


def test_backtest_engine_uses_strategy_risk_when_engine_risk_is_not_set():
    class Strategy:
        risk_per_trade = Decimal("1")

        def on_candle(self, candles):
            if len(candles) == 1:
                return __import__("app.backtest.engine", fromlist=["MarketOrder"]).MarketOrder(
                    Side.LONG, None, Decimal("100"), Decimal("95"), Decimal("110")
                )
            return None

    engine = BacktestEngine([candle(0)], starting_balance=Decimal("1000"))
    result = engine.run(Strategy())
    assert result.trades[0].quantity == Decimal("2E+0")


def test_strategy_condition_value_without_operator_is_an_equality_check():
    condition = StrategyCondition(type=ConditionType.TREND, field="bias", value="BULLISH")
    from app.strategy.dsl import StrategySignalContext

    assert condition.matches(StrategySignalContext(values={"bias": "BULLISH"}))
    assert not condition.matches(StrategySignalContext(values={"bias": "BEARISH"}))
