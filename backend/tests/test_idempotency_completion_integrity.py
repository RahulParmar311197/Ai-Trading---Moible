from decimal import Decimal
import json

import pytest

from app.brokers.base import BrokerOrder, BrokerOrderStatus, BrokerOrderType, BrokerSide
from app.brokers.durable_idempotency import DurableBrokerIdempotencyStore
from app.brokers.idempotency import BrokerIdempotencyStore, IdempotencyConflict, IdempotencyPending


def order(*, client_order_id: str = "client-1", quantity: int = 5, symbol: str = "NIFTY") -> BrokerOrder:
    return BrokerOrder(order_id="local-1", client_order_id=client_order_id, symbol=symbol, side=BrokerSide.BUY, order_type=BrokerOrderType.MARKET, quantity=quantity, status=BrokerOrderStatus.NEW)


def filled_result(request: BrokerOrder, *, broker_order_id: str = "broker-1") -> BrokerOrder:
    return request.model_copy(update={"order_id": broker_order_id, "filled_quantity": request.quantity, "average_price": Decimal("100"), "status": BrokerOrderStatus.FILLED})


def test_in_memory_completion_preserves_reservation_and_rejects_mismatch() -> None:
    store = BrokerIdempotencyStore()
    submitted = order()
    store.begin(submitted)
    mismatched = filled_result(submitted.model_copy(update={"quantity": 10}))
    with pytest.raises(IdempotencyConflict, match="broker result does not match"):
        store.complete(submitted, mismatched)
    with pytest.raises(IdempotencyPending, match="unresolved broker submission"):
        store.begin(submitted)


def test_in_memory_completion_can_bootstrap_authoritative_recovery() -> None:
    store = BrokerIdempotencyStore()
    submitted = order()
    result = filled_result(submitted)

    assert store.complete(result, result) == result
    assert store.begin(submitted) == result


class FakeDurableDb:
    def __init__(self) -> None:
        self.row = None
        self.returning_calls = 0
        self.update_calls = 0

    def execute_returning(self, query: str, params: dict):
        self.returning_calls += 1
        key = params["client_order_id"]
        if "DO NOTHING" in query:
            if self.row is not None:
                return None
            self.row = {"client_order_id": key, "fingerprint": params["fingerprint"], "result": None}
            return {"client_order_id": key}

        if self.row is None:
            self.row = {
                "client_order_id": key,
                "fingerprint": params["fingerprint"],
                "result": json.loads(str(params["result"])),
            }
            return {"result": self.row["result"]}
        if self.row["fingerprint"] != params["fingerprint"]:
            return None
        incoming = json.loads(str(params["result"]))
        if self.row["result"] is not None and self.row["result"] != incoming:
            return None
        self.row["result"] = incoming
        return {"result": self.row["result"]}

    def execute(self, query: str, params: dict) -> None:
        self.update_calls += 1
        if query.lstrip().startswith("DELETE"):
            self.row = None

    def fetch_one(self, query: str, params: dict):
        if self.row is None:
            return None
        if "fingerprint" in params and self.row["fingerprint"] != params["fingerprint"]:
            return None
        return self.row


def test_durable_completion_rejects_mismatched_result_before_persistence() -> None:
    db = FakeDurableDb()
    store = DurableBrokerIdempotencyStore(db)
    submitted = order()
    assert store.begin(submitted) is None
    mismatched = filled_result(submitted.model_copy(update={"symbol": "BANKNIFTY"}))
    with pytest.raises(IdempotencyConflict, match="broker result does not match"):
        store.complete(submitted, mismatched)
    assert db.update_calls == 0
    assert db.returning_calls == 1


def test_durable_completion_accepts_matching_result() -> None:
    db = FakeDurableDb()
    store = DurableBrokerIdempotencyStore(db)
    submitted = order()
    assert store.begin(submitted) is None
    result = filled_result(submitted)
    assert store.complete(submitted, result) == result
    assert db.returning_calls == 2
    assert db.update_calls == 0
    assert store.begin(submitted) == result


def test_durable_completion_can_bootstrap_authoritative_recovery() -> None:
    db = FakeDurableDb()
    store = DurableBrokerIdempotencyStore(db)
    result = filled_result(order())

    assert store.complete(result, result) == result
    assert store.begin(order()) == result


def test_durable_completion_rejects_overwriting_existing_terminal_result() -> None:
    db = FakeDurableDb()
    store = DurableBrokerIdempotencyStore(db)
    submitted = order()
    first = filled_result(submitted, broker_order_id="broker-1")
    different = filled_result(submitted, broker_order_id="broker-2")

    assert store.complete(submitted, first) == first
    with pytest.raises(IdempotencyConflict, match="different result"):
        store.complete(submitted, different)
    assert store.begin(submitted) == first
