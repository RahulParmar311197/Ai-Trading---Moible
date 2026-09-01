"""Reusable declarative strategy adapter for replay/backtesting.

This module connects the existing Strategy DSL to the existing BacktestStrategy
protocol. It deliberately produces only a MarketOrder after deterministic SMC
facts and DSL conditions match; it never talks to a broker or authorizes live
execution.
"""

from decimal import Decimal
from typing import Sequence

from app.backtest.engine import MarketOrder
from app.market.models import Candle
from app.smc.engine import SmcEngine

from .dsl import StrategyDefinition, StrategySignalContext


class DslBacktestStrategy:
    """Evaluate one validated StrategyDefinition against visible candles only."""

    def __init__(self, definition: StrategyDefinition, smc: SmcEngine | None = None) -> None:
        self.definition = definition
        self.smc = smc or SmcEngine()

    @property
    def risk_per_trade(self) -> Decimal:
        return self.definition.risk.risk_percent

    def on_candle(self, candles: Sequence[Candle]) -> MarketOrder | None:
        if not candles:
            return None
        current = candles[-1]
        analysis = self.smc.analyze(list(candles))
        context = StrategySignalContext.from_smc_signal(analysis.signal)
        context.values.update(
            {
                "symbol": current.instrument_id,
                "timeframe": current.timeframe.value,
                "close": current.close,
                "current_zone": analysis.current_zone,
                "price": current.close,
            }
        )

        if current.timeframe != self.definition.timeframe:
            return None
        if self.definition.market != current.instrument_id:
            return None
        if self.definition.direction is not None:
            expected_bias = self.definition.direction.upper()
            if context.get("bias") != expected_bias:
                return None
        if not self.definition.matches(context):
            return None

        entry = self.definition.entry
        price = self._decimal(entry.get("price"), current.close)
        stop = self._resolve_stop(entry, price)
        target = self._resolve_target(entry, price, stop)
        quantity = self._positive_decimal(entry.get("quantity"))
        if self.definition.direction == "bullish":
            side = "LONG"
        elif self.definition.direction == "bearish":
            side = "SHORT"
        else:
            return None

        if stop is not None and target is not None:
            distance = abs(price - stop)
            if distance == 0:
                return None
            rr = abs(target - price) / distance
            minimum_rr = self.definition.risk.minimum_rr
            if minimum_rr is not None and rr < minimum_rr:
                return None

        from app.backtest.engine import Side

        return MarketOrder(Side(side), quantity, price, stop, target)

    @staticmethod
    def _decimal(value: object, default: Decimal) -> Decimal:
        if value is None:
            return default
        return Decimal(str(value))

    @staticmethod
    def _positive_decimal(value: object) -> Decimal | None:
        if value is None:
            return None
        result = Decimal(str(value))
        if result <= 0:
            raise ValueError("strategy entry quantity must be positive")
        return result

    def _resolve_stop(self, entry: dict[str, object], price: Decimal) -> Decimal | None:
        if entry.get("stop_price") is not None:
            return self._decimal(entry["stop_price"], price)
        if entry.get("stop_distance") is not None:
            distance = self._decimal(entry["stop_distance"], Decimal("0"))
            if distance <= 0:
                raise ValueError("strategy stop_distance must be positive")
            return price - distance if self.definition.direction == "bullish" else price + distance
        return None

    def _resolve_target(self, entry: dict[str, object], price: Decimal, stop: Decimal | None) -> Decimal | None:
        if entry.get("target_price") is not None:
            return self._decimal(entry["target_price"], price)
        if stop is None or self.definition.risk.minimum_rr is None:
            return None
        distance = abs(price - stop) * self.definition.risk.minimum_rr
        return price + distance if self.definition.direction == "bullish" else price - distance
