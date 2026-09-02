from decimal import Decimal

from app.execution import DeterministicExecutionGate, RiskLimits, RiskSnapshot
from app.paper.models import Order, OrderSide, OrderType


def order(quantity: int, side: OrderSide = OrderSide.BUY) -> Order:
    return Order(order_id="test", symbol="NIFTY", side=side, order_type=OrderType.MARKET, quantity=quantity)


def snapshot(**kwargs) -> RiskSnapshot:
    values = dict(balance=Decimal("100000"), realized_pnl=Decimal("0"), halted=False, position_quantity=0)
    values.update(kwargs)
    return RiskSnapshot(**values)


def test_gate_approves_order_inside_all_limits() -> None:
    gate = DeterministicExecutionGate(RiskLimits(max_order_notional=Decimal("20000"), max_position_quantity=100, max_daily_loss=Decimal("5000")))
    decision = gate.evaluate(order(10), Decimal("1000"), snapshot())
    assert decision.approved is True
    assert decision.reason == "approved"


def test_gate_rejects_halted_account() -> None:
    gate = DeterministicExecutionGate(RiskLimits())
    decision = gate.evaluate(order(1), Decimal("100"), snapshot(halted=True))
    assert decision == decision.__class__(False, "risk halt is active")


def test_gate_rejects_notional_position_and_daily_loss_limits() -> None:
    gate = DeterministicExecutionGate(RiskLimits(max_order_notional=Decimal("1000"), max_position_quantity=5, max_daily_loss=Decimal("500")))
    assert gate.evaluate(order(11), Decimal("100"), snapshot()).approved is False
    assert gate.evaluate(order(6), Decimal("100"), snapshot()).approved is False
    assert gate.evaluate(order(1), Decimal("100"), snapshot(realized_pnl=Decimal("-500"))).approved is False


def test_gate_accounts_for_existing_short_position() -> None:
    gate = DeterministicExecutionGate(RiskLimits(max_position_quantity=5))
    decision = gate.evaluate(order(2, OrderSide.SELL), Decimal("100"), snapshot(position_quantity=-4))
    assert decision.approved is False
