from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


class RiskOrder(Protocol):
    quantity: int
    side: object


@dataclass(frozen=True)
class RiskLimits:
    max_order_notional: Decimal | None = None
    max_position_quantity: int | None = None
    max_daily_loss: Decimal | None = None

    def __post_init__(self) -> None:
        for name, value in (("max_order_notional", self.max_order_notional), ("max_daily_loss", self.max_daily_loss)):
            if value is not None and value <= 0:
                raise ValueError(f"{name} must be positive")
        if self.max_position_quantity is not None and self.max_position_quantity <= 0:
            raise ValueError("max_position_quantity must be positive")


@dataclass(frozen=True)
class RiskSnapshot:
    balance: Decimal
    realized_pnl: Decimal
    halted: bool
    position_quantity: int = 0


@dataclass(frozen=True)
class ExecutionDecision:
    approved: bool
    reason: str


class DeterministicExecutionGate:
    """Pure pre-trade gate; it cannot submit orders to any broker."""

    def __init__(self, limits: RiskLimits) -> None:
        self.limits = limits

    def evaluate(self, order: RiskOrder, market_price: Decimal, snapshot: RiskSnapshot) -> ExecutionDecision:
        if snapshot.halted:
            return ExecutionDecision(False, "risk halt is active")
        if market_price <= 0:
            return ExecutionDecision(False, "market price must be positive")
        if order.quantity <= 0:
            return ExecutionDecision(False, "order quantity must be positive")
        if self.limits.max_daily_loss is not None and snapshot.realized_pnl <= -self.limits.max_daily_loss:
            return ExecutionDecision(False, "maximum daily loss reached")
        if self.limits.max_order_notional is not None and market_price * order.quantity > self.limits.max_order_notional:
            return ExecutionDecision(False, "order exceeds maximum notional")
        if self.limits.max_position_quantity is not None:
            side = getattr(order.side, "value", order.side)
            signed = order.quantity if str(side).upper() == "BUY" else -order.quantity
            if abs(snapshot.position_quantity + signed) > self.limits.max_position_quantity:
                return ExecutionDecision(False, "order exceeds maximum position quantity")
        return ExecutionDecision(True, "approved")
