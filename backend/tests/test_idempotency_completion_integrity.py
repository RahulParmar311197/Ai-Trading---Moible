from decimal import Decimal

import pytest

from app.brokers.base import BrokerOrder, BrokerOrderStatus, BrokerOrderType, BrokerSide
from app.brokers.durable_idempotency import DurableBrokerIdempotencyStore
from app.brokers.idempotency import BrokerIdempotencyStore, IdempotencyConflict, IdempotencyPending


def order(*, client_order_id: str = "client-1", quantity: int = 5, symbol: str = "NIFTY") -> BrokerOrder:
    return BrokerOrder(
        order_id="local-1",
        client_order_id=client_order_id,
        symbol=symbol,
        side=BrokerSide.BUY,
        order_type=BrokerOrderType.MARKET,
        quantity=quantity,
        status=BrokerOrderStatus.NEW,
    )


def filled_result(request: BrokerOrder, *, quantity: int | None = None) -> BrokerOrder:
    filled_quantity = request.quantity if quantity is None else quantity
    return request.model_copy(
        update={
            "order_id": "broker-1",
            "filled_quantity": filled_quantity,
            "average_price": Decimal("100"),
            "status": BrokerOrderStatus.FILLED,
        }
    )


def test_in_memory_completion_preserves_reservation_and_rejects_mismatch() -> None:
    store = BrokerIdempotencyStore()
    submitted = order()
    store.begin(submitted)

    mismatched = filled_result(submitted.model_copy(update={"quantity": 10}))
    with pytest.raises(IdempotencyConflict, match="broker result does not match"):
        store.complete(submitted, mismatched)

    with pytest.raises(IdempotencyPending, match="unresolved broker submission"):
        store.begin(submitted)


def test_in_memory_completion_requires_existing_reservation() -> None:
    store = BrokerIdempotencyStore()
    submitted = order()

    with pytest.raises(RuntimeError, match="reservation missing"):
        store.complete(submitted, filled_result(submitted))


class FakeDurableDb:
    def __init__(self) -> None:
        self.row = None
        self.update_calls = 0

    def execute_returning(self, _query: str, params: dict):
        if self.row is None:
            self.row = {
                "client_order_id": params["client_order_id"],
                "fingerprint": params["fingerprint"],
                "result": None,
            }
            return {"client_order_id": params["client_order_id"]}
        return None

    def execute(self, _query: str, params: dict) -> None:
        self.update_calls += 1
        if self.row is None:
            return
        if self.row["client_order_id"] == params["client_order_id"] and self.row["fingerprint"] == params["fingerprint"]:
            self.row["result"] = params["result"]

    def fetch_one(self, query: str, params: dict):
        if "SELECT fingerprint, result" in query:
            return self.row
        if "result IS NOT NULL" in query and self.row is not None:
            if (
                self.row["client_order_id"] == params["client_order_id"]
                and self.row["fingerprint"] == params["fingerprint"]
                and self.row["result"] is not None
            ):
                return {"client_order_id": self.row["client_order_id"]}
        return None


def test_durable_completion_rejects_mismatched_result_before_persistence() -> None:
    db = FakeDurableDb()
    store = DurableBrokerIdempotencyStore(db)
    submitted = order()
    assert store.begin(submitted) is None

    mismatched = filled_result(submitted.model_copy(update={"symbol": "BANKNIFTY"}))
    with pytest.raises(IdempotencyConflict, match="broker result does not match"):
        store.complete(submitted, mismatched)

    assert db.update_calls == 0


def test_durable_completion_accepts_matching_result() -> None:
    db = FakeDurableDb()
    store = DurableBrokerIdempotencyStore(db)
    submitted = order()
    assert store.begin(submitted) is None
    result = filled_result(submitted)

    assert store.complete(submitted, result) == result
    assert db.update_calls == 1
    assert store.begin(submitted) == result
