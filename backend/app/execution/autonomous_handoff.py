from __future__ import annotations

from decimal import Decimal

from app.brokers.base import BrokerOrder, BrokerOrderType, BrokerSide, BrokerOrderStatus

from .autonomous import ExecutionIntent


class AutonomousIntentHandoffError(ValueError):
    """Raised when an autonomous intent cannot be safely materialized as an order."""


def build_broker_order(intent: ExecutionIntent, *, client_order_id: str) -> BrokerOrder:
    """Materialize an approved intent without contacting or activating a broker.

    The caller supplies the client-order identifier so durable idempotency remains
    an explicit execution-layer responsibility. This function never submits,
    authorizes, activates, or mutates broker state.
    """
    if not intent.session_id.strip():
        raise AutonomousIntentHandoffError("intent session id must be non-empty")
    if not intent.strategy_id.strip():
        raise AutonomousIntentHandoffError("intent strategy id must be non-empty")
    if not intent.symbol.strip():
        raise AutonomousIntentHandoffError("intent symbol must be non-empty")
    if not client_order_id.strip():
        raise AutonomousIntentHandoffError("client order id must be non-empty")
    if not intent.risk_decision.approved:
        raise AutonomousIntentHandoffError("only an approved deterministic intent may be materialized")
    if intent.quantity <= 0:
        raise AutonomousIntentHandoffError("intent quantity must be positive")
    if not intent.market_price.is_finite() or intent.market_price <= 0:
        raise AutonomousIntentHandoffError("intent market price must be finite and positive")

    try:
        side = BrokerSide(intent.side.upper())
    except ValueError as exc:
        raise AutonomousIntentHandoffError("intent side must be BUY or SELL") from exc

    return BrokerOrder(
        order_id=client_order_id,
        client_order_id=client_order_id,
        symbol=intent.symbol,
        side=side,
        order_type=BrokerOrderType.MARKET,
        quantity=intent.quantity,
        status=BrokerOrderStatus.NEW,
        average_price=Decimal(str(intent.market_price)),
    )
