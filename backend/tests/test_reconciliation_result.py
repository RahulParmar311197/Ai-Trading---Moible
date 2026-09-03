from decimal import Decimal

import pytest

from app.brokers.base import BrokerOrder, BrokerOrderStatus, BrokerOrderType, BrokerReconciliation, BrokerSide


def order(status: BrokerOrderStatus, filled_quantity: int = 0) -> BrokerOrder:
    return BrokerOrder(
        order_id="broker-1",
        client_order_id="client-1",
        symbol="NIFTY",
        side=BrokerSide.BUY,
        order_type=BrokerOrderType.MARKET,
        quantity=5,
        filled_quantity=filled_quantity,
        average_price=Decimal("100") if filled_quantity else None,
        status=status,
    )


def test_reconciliation_can_carry_authoritative_broker_order() -> None:
    broker_order = order(BrokerOrderStatus.FILLED, 5)
    result = BrokerReconciliation(
        client_order_id="client-1",
        broker_status=broker_order.status,
        matched=True,
        broker_order=broker_order,
    )
    assert result.broker_order == broker_order


def test_reconciliation_rejects_inconsistent_embedded_order() -> None:
    broker_order = order(BrokerOrderStatus.FILLED, 5)
    with pytest.raises(ValueError, match="client order id"):
        BrokerReconciliation(
            client_order_id="other-client",
            broker_status=broker_order.status,
            matched=True,
            broker_order=broker_order,
        )
