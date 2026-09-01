from decimal import Decimal

import pytest

from app.market.models import Timeframe
from app.strategy.dsl import (
    ConditionType,
    Operator,
    StrategyCondition,
    StrategyDefinition,
    StrategySignalContext,
)


def test_strategy_definition_matches_structured_context():
    strategy = StrategyDefinition(
        name="Bullish Liquidity Sweep",
        market="NIFTY",
        timeframe=Timeframe.M15,
        direction="bullish",
        conditions=[
            StrategyCondition(type=ConditionType.LIQUIDITY_SWEEP, field="sell_side_sweep"),
            StrategyCondition(type=ConditionType.MSS, field="bullish_mss"),
            StrategyCondition(type=ConditionType.FVG, field="bullish_fvg"),
        ],
        entry={"type": "fvg_retest"},
        risk={"risk_percent": Decimal("0.5"), "minimum_rr": Decimal("2")},
    )
    assert strategy.matches(StrategySignalContext(values={"sell_side_sweep": True, "bullish_mss": True, "bullish_fvg": True}))
    assert not strategy.matches(StrategySignalContext(values={"sell_side_sweep": True, "bullish_mss": False, "bullish_fvg": True}))


def test_nested_boolean_operators_are_validated_and_deterministic():
    condition = StrategyCondition(
        type=ConditionType.BOS,
        operator=Operator.AND,
        conditions=[
            StrategyCondition(type=ConditionType.BOS, field="bullish_bos"),
            StrategyCondition(type=ConditionType.FVG, field="bullish_fvg"),
        ],
    )
    context = StrategySignalContext(values={"bullish_bos": True, "bullish_fvg": True})
    assert condition.matches(context) is True
    assert condition.matches(StrategySignalContext(values={"bullish_bos": True, "bullish_fvg": False})) is False


def test_comparison_and_range_operators_are_safe_for_missing_fields():
    greater = StrategyCondition(type=ConditionType.VOLATILITY, operator=Operator.GREATER_THAN, field="atr", value=Decimal("10"))
    within = StrategyCondition(type=ConditionType.VOLUME, operator=Operator.WITHIN, field="volume", value=[100, 200])
    assert greater.matches(StrategySignalContext()) is False
    assert within.matches(StrategySignalContext(values={"volume": 150})) is True


def test_not_requires_exactly_one_child():
    with pytest.raises(ValueError, match="exactly one"):
        StrategyCondition(
            type=ConditionType.BOS,
            operator=Operator.NOT,
            conditions=[
                StrategyCondition(type=ConditionType.BOS, field="a"),
                StrategyCondition(type=ConditionType.BOS, field="b"),
            ],
        )
