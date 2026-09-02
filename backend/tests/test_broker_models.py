from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.brokers.base import BrokerOrder, BrokerOrderStatus, BrokerOrderType, BrokerPosition, BrokerSide


def make_order(**changes) -> BrokerOrder:
    values = dict(
        order_id="broker-1",
        client_order_id="client-1",
        symbol="NIFTY",
        side=BrokerSide.BUY,
        order_type=BrokerOrderType.MARKET,
        quantity=10,
        filled_quantity=0,
        status=BrokerOrderStatus.OPEN,
    )
    values.update(changes)
    return BrokerOrder(**values)


def make_position(**changes) -> BrokerPosition:
    values = dict(
        symbol="NIFTY",
        quantity=10,
        average_price=Decimal("100"),
    )
    values.update(changes)
    return BrokerPosition(**values)


def test_broker_order_rejects_filled_quantity_above_order_quantity() -> None:
    with pytest.raises(ValidationError, match="filled quantity cannot exceed order quantity"):
        make_order(filled_quantity=11)


def test_broker_order_requires_complete_fill_for_filled_status() -> None:
    with pytest.raises(ValidationError, match="filled order must have complete fill quantity"):
        make_order(filled_quantity=9, status=BrokerOrderStatus.FILLED)


def test_broker_order_requires_strict_partial_fill_for_partial_status() -> None:
    with pytest.raises(ValidationError, match="partially filled order must have a partial fill quantity"):
        make_order(filled_quantity=0, status=BrokerOrderStatus.PARTIALLY_FILLED)
    with pytest.raises(ValidationError, match="partially filled order must have a partial fill quantity"):
        make_order(filled_quantity=10, status=BrokerOrderStatus.PARTIALLY_FILLED)


def test_broker_order_rejects_non_finite_or_non_positive_average_price() -> None:
    with pytest.raises(ValidationError, match="finite"):
        make_order(average_price=Decimal("NaN"))
    with pytest.raises(ValidationError, match="average price must be finite and positive"):
        make_order(average_price=Decimal("0"))


def test_broker_position_rejects_non_finite_financial_values() -> None:
    with pytest.raises(ValidationError, match="finite"):
        make_position(average_price=Decimal("Infinity"))
    with pytest.raises(ValidationError, match="finite"):
        make_position(realized_pnl=Decimal("NaN"))
    with pytest.raises(ValidationError, match="finite"):
        make_position(unrealized_pnl=Decimal("Infinity"))
