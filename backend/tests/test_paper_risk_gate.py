from decimal import Decimal

import pytest

from app.execution import DeterministicExecutionGate, RiskLimits
from app.paper import PaperBroker
from app.paper.models import Order, OrderSide, OrderType


def make_order(order_id: str, quantity: int) -> Order:
    return Order(
        order_id=order_id,
        symbol="NIFTY",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=quantity,
    )


def test_paper_broker_risk_gate_rejects_before_order_persistence() -> None:
    gate = DeterministicExecutionGate(RiskLimits(max_order_notional=Decimal("1000")))
    paper = PaperBroker(risk_gate=gate)

    with pytest.raises(ValueError, match="order exceeds maximum notional"):
        paper.place_order(make_order("blocked", 11), Decimal("100"))

    assert "blocked" not in paper.orders
    assert paper.fills == []


def test_paper_broker_risk_gate_allows_order_inside_limits() -> None:
    gate = DeterministicExecutionGate(RiskLimits(max_order_notional=Decimal("1000"), max_position_quantity=10))
    paper = PaperBroker(risk_gate=gate)

    fill = paper.place_order(make_order("allowed", 10), Decimal("100"))

    assert fill is not None
    assert paper.orders["allowed"].filled_quantity == 10
    assert paper.positions["NIFTY"].quantity == 10
