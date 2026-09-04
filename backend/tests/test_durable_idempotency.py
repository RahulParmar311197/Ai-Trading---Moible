import json
from decimal import Decimal

import pytest

from app.brokers.base import BrokerOrder, BrokerOrderStatus, BrokerOrderType, BrokerSide
from app.brokers.durable_idempotency import DurableBrokerIdempotencyStore
from app.brokers.idempotency import IdempotencyConflict, IdempotencyPending


class FakeDb:
    def __init__(self) -> None:
        self.rows: dict[str, dict[str, object]] = {}
        self.executed: list[tuple[str, dict[str, object]]] = []

    def execute_returning(self, sql: str, params: dict[str, object]) -> object | None:
        self.executed.append((sql, params))
        key = str(params["client_order_id"])
        if "DO NOTHING" in sql:
            if key in self.rows:
                return None
            self.rows[key] = {"fingerprint": params["fingerprint"], "result": None}
            return {"client_order_id": key}

        row = self.rows.get(key)
        if row is None:
            self.rows[key] = {
                "fingerprint": params["fingerprint"],
                "result": json.loads(str(params["result"])),
            }
            return {"result": self.rows[key]["result"]}
        if row["fingerprint"] != params["fingerprint"]:
            return None
        incoming = json.loads(str(params["result"]))
        if row["result"] is not None and row["result"] != incoming:
            return None
        row["result"] = incoming
        return {"result": row["result"]}

    def fetch_one(self, sql: str, params: dict[str, object]) -> dict[str, object] | None:
        key = str(params["client_order_id"])
        row = self.rows.get(key)
        if row is None:
            return None
        if "fingerprint" in params and row["fingerprint"] != params["fingerprint"]:
            return None
        return row

    def execute(self, sql: str, params: dict[str, object]) -> None:
        self.executed.append((sql, params))
        if sql.lstrip().startswith("DELETE"):
            self.rows.pop(str(params["client_order_id"]), None)


def order(*, symbol: str = "NIFTY", client_order_id: str = "client-1") -> BrokerOrder:
    return BrokerOrder(
        order_id="local-1",
        client_order_id=client_order_id,
        symbol=symbol,
        side=BrokerSide.BUY,
        order_type=BrokerOrderType.MARKET,
        quantity=1,
        average_price=None,
        status=BrokerOrderStatus.NEW,
    )


def result(order_id: str = "broker-1") -> BrokerOrder:
    return BrokerOrder(
        order_id=order_id,
        client_order_id="client-1",
        symbol="NIFTY",
        side=BrokerSide.BUY,
        order_type=BrokerOrderType.MARKET,
        quantity=1,
        filled_quantity=1,
        average_price=Decimal("100"),
        status=BrokerOrderStatus.FILLED,
    )


def test_durable_store_rejects_reuse_while_submission_is_unresolved() -> None:
    db = FakeDb()
    store = DurableBrokerIdempotencyStore(db)
    request = order()

    assert store.begin(request) is None
    with pytest.raises(IdempotencyPending, match="unresolved broker submission"):
        store.begin(request)


def test_durable_store_returns_cached_result_after_completion() -> None:
    db = FakeDb()
    store = DurableBrokerIdempotencyStore(db)
    request = order()
    broker_result = result()

    assert store.begin(request) is None
    assert store.complete(request, broker_result) == broker_result
    assert store.begin(request) == broker_result


def test_durable_store_rejects_conflicting_reuse() -> None:
    db = FakeDb()
    store = DurableBrokerIdempotencyStore(db)
    request = order()
    conflicting = order(symbol="BANKNIFTY")

    assert store.begin(request) is None
    with pytest.raises(IdempotencyConflict, match="different order"):
        store.begin(conflicting)


def test_durable_store_clear_allows_reuse_only_after_explicit_reconciliation() -> None:
    db = FakeDb()
    store = DurableBrokerIdempotencyStore(db)
    request = order()

    assert store.begin(request) is None
    with pytest.raises(IdempotencyPending):
        store.begin(request)

    store.clear(request.client_order_id)
    assert store.begin(request) is None


def test_durable_store_does_not_overwrite_existing_terminal_result() -> None:
    db = FakeDb()
    store = DurableBrokerIdempotencyStore(db)
    request = order()
    first = result("broker-1")
    different = result("broker-2")

    assert store.begin(request) is None
    assert store.complete(request, first) == first

    with pytest.raises(IdempotencyConflict, match="different result"):
        store.complete(request, different)

    assert store.begin(request) == first
    completion_statements = [sql for sql, _ in db.executed if "DO UPDATE" in sql]
    assert len(completion_statements) == 2
    assert all("result IS NULL" in sql for sql in completion_statements)
