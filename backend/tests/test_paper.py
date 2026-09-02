from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.paper import Fill, Order, OrderSide, OrderStatus, OrderType, PaperBroker, Position


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
    assert broker.fills[-1].price == Decimal("110")
    assert broker.balance == Decimal("10100")
    assert broker.realized_pnl_total == Decimal("100")


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


def test_order_and_position_risk_limits_reject_before_fill() -> None:
    broker = PaperBroker(max_order_notional=Decimal("500"), max_position_quantity=10)
    with pytest.raises(ValueError, match="notional"):
        broker.place_order(order("1", OrderSide.BUY, 6), Decimal("100"))
    broker.place_order(order("2", OrderSide.BUY, 5), Decimal("100"))
    with pytest.raises(ValueError, match="position limit"):
        broker.place_order(order("3", OrderSide.BUY, 6), Decimal("100"))


def test_kill_switch_rejects_new_orders_until_cleared() -> None:
    broker = PaperBroker()
    broker.kill_switch()
    with pytest.raises(ValueError, match="halted"):
        broker.place_order(order("1", OrderSide.BUY), Decimal("100"))
    broker.clear_kill_switch()
    assert broker.place_order(order("2", OrderSide.BUY), Decimal("100")) is not None


def test_order_rejects_inconsistent_fill_state() -> None:
    with pytest.raises(ValidationError, match="filled quantity"):
        Order(order_id="1", symbol="NIFTY", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=10, filled_quantity=11)
    with pytest.raises(ValidationError, match="complete fill"):
        Order(order_id="2", symbol="NIFTY", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=10, status=OrderStatus.FILLED)
    with pytest.raises(ValidationError, match="partial fill"):
        Order(order_id="3", symbol="NIFTY", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=10, status=OrderStatus.PARTIALLY_FILLED, filled_quantity=10)


def test_paper_financial_models_reject_non_finite_values() -> None:
    with pytest.raises(ValidationError):
        Fill(order_id="1", quantity=1, price=Decimal("NaN"))
    with pytest.raises(ValidationError):
        Position(symbol="NIFTY", quantity=1, average_price=Decimal("100"), realized_pnl=Decimal("NaN"))
    with pytest.raises(ValidationError):
        Order(order_id="1", symbol="NIFTY", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=1, average_fill_price=Decimal("NaN"))


def test_position_mark_rejects_non_finite_or_non_positive_price() -> None:
    position = Position(symbol="NIFTY", quantity=1, average_price=Decimal("100"))
    with pytest.raises(ValueError, match="finite and positive"):
        position.mark(Decimal("NaN"))
    with pytest.raises(ValueError, match="finite and positive"):
        position.mark(Decimal("0"))
