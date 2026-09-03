from __future__ import annotations

from typing import Protocol

from app.brokers.base import BrokerOrder

from .autonomous import ExecutionIntent
from .autonomous_handoff import build_broker_order
from .controlled import ControlledExecutionError
from .gate import RiskSnapshot


class ControlledExecutor(Protocol):
    async def submit(
        self,
        order: BrokerOrder,
        *,
        market_price: object,
        snapshot: RiskSnapshot,
    ) -> BrokerOrder: ...


class AutonomousExecutionBridgeError(ControlledExecutionError):
    """Raised when an autonomous intent cannot safely reach controlled execution."""


async def submit_autonomous_intent(
    executor: ControlledExecutor,
    intent: ExecutionIntent,
    *,
    client_order_id: str,
    snapshot: RiskSnapshot,
) -> BrokerOrder:
    """Submit an approved autonomous intent only through the controlled executor.

    This bridge performs no activation and no direct broker call. The controlled
    executor remains authoritative for startup, activation, emergency control,
    fresh position state, deterministic risk, idempotency, confirmation, and
    post-fill synchronization.
    """
    if not intent.portfolio_risk.approved:
        raise AutonomousExecutionBridgeError("only a portfolio-risk-approved intent may reach controlled execution")
    order = build_broker_order(intent, client_order_id=client_order_id)
    try:
        return await executor.submit(order, market_price=intent.market_price, snapshot=snapshot)
    except ControlledExecutionError:
        raise
