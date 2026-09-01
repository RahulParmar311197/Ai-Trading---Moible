"""Validated, declarative strategy DSL primitives.

The DSL describes conditions and risk constraints; it never contains executable
Python/code and therefore cannot directly authorize broker orders.
"""

from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.market.models import Timeframe
from app.smc.models import SignalContext


class ConditionType(StrEnum):
    TREND = "trend"
    BOS = "bos"
    MSS = "mss"
    CHOCH = "choch"
    LIQUIDITY_SWEEP = "liquidity_sweep"
    FVG = "fvg"
    ORDER_BLOCK = "order_block"
    PREMIUM_DISCOUNT = "premium_discount"
    VOLUME = "volume"
    VOLATILITY = "volatility"
    SESSION = "session"
    INDICATOR = "indicator"
    OPTIONS_IV = "options_iv"
    OPTIONS_OI = "options_oi"
    OPTIONS_GREEKS = "options_greeks"


class Operator(StrEnum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    GREATER_THAN = "GREATER_THAN"
    LESS_THAN = "LESS_THAN"
    CROSSES = "CROSSES"
    TOUCHES = "TOUCHES"
    WITHIN = "WITHIN"


class StrategySignalContext(BaseModel):
    """Structured facts available to a strategy evaluator."""

    values: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_smc_signal(cls, signal: SignalContext) -> "StrategySignalContext":
        """Adapt deterministic SMC facts without giving the DSL execution authority."""
        return cls(
            values={
                "bias": signal.bias.value,
                "bos": signal.bos,
                "mss": signal.mss,
                "choch": signal.choch,
                "liquidity_sweep": signal.liquidity_sweep,
                "fvg": signal.fvg,
                "order_block": signal.order_block,
                "score": signal.score,
                "reasons": signal.reasons,
            }
        )

    def get(self, key: str) -> Any:
        return self.values.get(key)


class StrategyCondition(BaseModel):
    type: ConditionType
    operator: Operator | None = None
    field: str | None = None
    value: Any = None
    conditions: list["StrategyCondition"] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_shape(self) -> "StrategyCondition":
        if self.operator in (Operator.AND, Operator.OR, Operator.NOT):
            if not self.conditions:
                raise ValueError(f"{self.operator.value} requires nested conditions")
            if self.operator is Operator.NOT and len(self.conditions) != 1:
                raise ValueError("NOT requires exactly one nested condition")
            return self
        if self.conditions:
            raise ValueError("nested conditions require AND, OR or NOT")
        if self.operator in (Operator.GREATER_THAN, Operator.LESS_THAN, Operator.CROSSES, Operator.TOUCHES, Operator.WITHIN):
            if not self.field:
                raise ValueError(f"{self.operator.value} requires field")
        return self

    def matches(self, context: StrategySignalContext) -> bool:
        if self.operator is Operator.AND:
            return all(condition.matches(context) for condition in self.conditions)
        if self.operator is Operator.OR:
            return any(condition.matches(context) for condition in self.conditions)
        if self.operator is Operator.NOT:
            return not self.conditions[0].matches(context)

        actual = context.get(self.field or self.type.value)
        if self.operator is None:
            return bool(actual)
        if self.operator is Operator.GREATER_THAN:
            return actual is not None and actual > self.value
        if self.operator is Operator.LESS_THAN:
            return actual is not None and actual < self.value
        if self.operator is Operator.TOUCHES:
            return actual == self.value
        if self.operator is Operator.WITHIN:
            if not isinstance(self.value, (list, tuple)) or len(self.value) != 2 or actual is None:
                return False
            return self.value[0] <= actual <= self.value[1]
        if self.operator is Operator.CROSSES:
            return isinstance(actual, bool) and actual
        return False


class StrategyRisk(BaseModel):
    risk_percent: Decimal = Field(gt=0, le=100)
    minimum_rr: Decimal | None = Field(default=None, gt=0)


class StrategyDefinition(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    market: str = Field(min_length=1, max_length=40)
    timeframe: Timeframe
    direction: str | None = Field(default=None, pattern="^(bullish|bearish|neutral)$")
    conditions: list[StrategyCondition] = Field(min_length=1)
    entry: dict[str, Any] = Field(default_factory=dict)
    risk: StrategyRisk

    def matches(self, context: StrategySignalContext) -> bool:
        return all(condition.matches(context) for condition in self.conditions)
