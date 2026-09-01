from decimal import Decimal

import pytest

from app.paper import Order, OrderSide, OrderStatus, OrderType, PaperBroker


def order(order_id: str, side: OrderSide, quantity: int = 10, order_type: OrderType = OrderType.MARKET, limit_price: Decimal | None = None) -> Order:
    return Order(
        order_id=order_id,
        symbol="NIFTY",
        side=side,
        order_type=order_type,
        quantity=quantity,
        limit_price=limit_price,
    )


def test_market_buy_creates_position_and_applies_slippage_and_fee() -> None:
    broker = PaperBroker(starting_balance=Decimal("10000"), fee_rate=Decimal("0.01"), slippage=Decimal("0.01"))
    fill = broker.place_order(order("1", OrderSide.BUY), Decimal("100"))
    assert fill is not None
    assert fill.price == Decimal("101.00")
    assert fill.fee == Decimal("10.10")
    assert broker.orders["1"].status is OrderStatus.FILLED
    assert broker.positions["NIFTY"].quantity == 10
    assert broker.positions["NIFTY"].average_price == Decimal("101.00")


def test_limit_order_waits_until_market_crosses() -> None:
    broker = PaperBroker()
    assert broker.place_order(order("1", OrderSide.BUY, order_type=OrderType.LIMIT, limit_price=Decimal("99")), Decimal("100")) is None
    assert broker.orders["1"].status is OrderStatus.NEW
    cancelled = broker.cancel_order("1")
    assert cancelled.status is OrderStatus.CANCELLED


def test_duplicate_order_ids_are_rejected() -> None:
    broker = PaperBroker()
    broker.place_order(order("1", OrderSide.BUY), Decimal("100"))
    with pytest.raises(ValueError, match="duplicate order id"):
        broker.place_order(order("1", OrderSide.BUY), Decimal("100"))


def test_closing_position_realizes_pnl() -> None:
    broker = PaperBroker(starting_balance=Decimal("10000"))
    broker.place_order(order("1", OrderSide.BUY, 10), Decimal("100"))
    broker.place_order(order("2", OrderSide.SELL, 10), Decimal("110"))
    assert "NIFTY" not in broker.positions
    # 10 shares * (110 - 100), before fees.
    assert broker.fills[-1].price == Decimal("110")
    assert broker.balance == Decimal("10100")


def test_short_position_marks_in_the_right_direction() -> None:
    broker = PaperBroker(starting_balance=Decimal("10000"))
    broker.place_order(order("1", OrderSide.SELL, 10), Decimal("100"))
    position = broker.mark_to_market("NIFTY", Decimal("90"))
    assert position is not None
    assert position.quantity == -10
    assert position.unrealized_pnl == Decimal("100")


def test_invalid_prices_are_rejected() -> None:
    broker = PaperBroker()
    with pytest.raises(ValueError):
        broker.place_order(order("1", OrderSide.BUY), Decimal("0"))
