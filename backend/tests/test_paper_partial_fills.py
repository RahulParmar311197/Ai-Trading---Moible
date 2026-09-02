from decimal import Decimal

import pytest

from app.paper import Order, OrderSide, OrderStatus, OrderType, PaperBroker


def test_market_order_can_complete_across_partial_fills() -> None:
    broker = PaperBroker()
    order = Order(order_id="partial-1", symbol="NIFTY", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=10)

    first = broker.place_order(order, Decimal("100"), fill_quantity=4)

    assert first is not None
    assert first.quantity == 4
    assert broker.orders["partial-1"].status is OrderStatus.PARTIALLY_FILLED
    assert broker.orders["partial-1"].filled_quantity == 4
    assert broker.orders["partial-1"].average_fill_price == Decimal("100")
    assert broker.positions["NIFTY"].quantity == 4

    second = broker.fill_order("partial-1", 6, Decimal("101"))

    assert second.quantity == 6
    assert broker.orders["partial-1"].status is OrderStatus.FILLED
    assert broker.orders["partial-1"].filled_quantity == 10
    assert broker.orders["partial-1"].average_fill_price == Decimal("100.6")
    assert broker.positions["NIFTY"].quantity == 10
    assert len(broker.fills) == 2


def test_process_market_fills_resting_limit_orders_in_stable_order() -> None:
    broker = PaperBroker()
    broker.place_order(
        Order(order_id="b", symbol="NIFTY", side=OrderSide.BUY, order_type=OrderType.LIMIT, quantity=5, limit_price=Decimal("100")),
        Decimal("105"),
    )
    broker.place_order(
        Order(order_id="a", symbol="NIFTY", side=OrderSide.BUY, order_type=OrderType.LIMIT, quantity=5, limit_price=Decimal("101")),
        Decimal("105"),
    )

    fills = broker.process_market("NIFTY", Decimal("100"), max_fill_quantity=2)

    assert [fill.order_id for fill in fills] == ["a", "b"]
    assert [fill.quantity for fill in fills] == [2, 2]
    assert broker.orders["a"].status is OrderStatus.PARTIALLY_FILLED
    assert broker.orders["b"].status is OrderStatus.PARTIALLY_FILLED

    broker.process_market("NIFTY", Decimal("99"))
    assert broker.orders["a"].status is OrderStatus.FILLED
    assert broker.orders["b"].status is OrderStatus.FILLED


def test_partial_fill_can_cancel_only_remaining_quantity() -> None:
    broker = PaperBroker()
    order = Order(order_id="cancel-1", symbol="NIFTY", side=OrderSide.BUY, order_type=OrderType.LIMIT, quantity=10, limit_price=Decimal("100"))
    broker.place_order(order, Decimal("100"), fill_quantity=3)

    cancelled = broker.cancel_order("cancel-1")

    assert cancelled.status is OrderStatus.CANCELLED
    assert cancelled.filled_quantity == 3
    with pytest.raises(ValueError, match="only open orders"):
        broker.fill_order("cancel-1", 1, Decimal("99"))
