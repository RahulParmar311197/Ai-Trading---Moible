"""PostgreSQL integration coverage for durable broker idempotency."""

import os
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import text

from app.brokers import BrokerOrder, BrokerOrderStatus, BrokerOrderType, BrokerSide
from app.brokers.durable_idempotency import DurableBrokerIdempotencyStore
from app.database.session import SQLAlchemyExecutor, create_database_engine


@pytest.mark.integration
def test_durable_idempotency_survives_repository_recreation() -> None:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not configured")

    root = Path(__file__).resolve().parents[2]
    engine = create_database_engine(database_url)
    with engine.begin() as connection:
        connection.exec_driver_sql((root / "database/migrations/009_broker_idempotency.sql").read_text())

    order = BrokerOrder(
        order_id="client-side-placeholder",
        client_order_id="integration-idempotency-order",
        symbol="NSE_EQ|TEST",
        side=BrokerSide.BUY,
        order_type=BrokerOrderType.MARKET,
        quantity=1,
        status=BrokerOrderStatus.NEW,
    )
    result = order.model_copy(update={"order_id": "broker-order-1", "status": BrokerOrderStatus.FILLED, "average_price": Decimal("100.25"), "filled_quantity": 1})

    first_store = DurableBrokerIdempotencyStore(SQLAlchemyExecutor(engine))
    assert first_store.begin(order) is None
    first_store.complete(order, result)

    second_store = DurableBrokerIdempotencyStore(SQLAlchemyExecutor(engine))
    cached = second_store.begin(order)
    assert cached is not None
    assert cached.order_id == result.order_id
    assert cached.status is result.status
    assert cached.average_price == result.average_price

    conflicting = order.model_copy(update={"quantity": 2})
    with pytest.raises(ValueError, match="already used"):
        second_store.begin(conflicting)

    with pytest.raises(RuntimeError, match="reservation missing"):
        second_store.complete(conflicting, result)

    with engine.begin() as connection:
        connection.execute(text("DELETE FROM broker_idempotency_keys WHERE client_order_id = :id"), {"id": order.client_order_id})
    engine.dispose()
