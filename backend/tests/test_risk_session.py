from decimal import Decimal

import pytest

from app.execution.risk_session import (
    PostgresRiskSessionBaselineStore,
    RiskSessionBaseline,
    RiskSessionBaselineConflict,
    RiskSessionBaselineMissing,
)


class FakeDb:
    def __init__(self, rows=None):
        self.rows = dict(rows or {})
        self.execute_returning_calls = 0

    def execute_returning(self, query, params):
        self.execute_returning_calls += 1
        session_id = params["session_id"]
        if session_id in self.rows:
            return None
        self.rows[session_id] = {
            "session_id": session_id,
            "daily_realized_pnl_baseline": params["daily_realized_pnl_baseline"],
        }
        return self.rows[session_id]

    def fetch_one(self, query, params):
        return self.rows.get(params["session_id"])


def test_initialize_is_idempotent_for_same_explicit_baseline() -> None:
    db = FakeDb()
    store = PostgresRiskSessionBaselineStore(db)
    baseline = RiskSessionBaseline("session-1", Decimal("125.50"))

    assert store.initialize(baseline) == baseline
    assert store.initialize(baseline) == baseline
    assert db.execute_returning_calls == 2


def test_initialize_rejects_conflicting_baseline() -> None:
    db = FakeDb()
    store = PostgresRiskSessionBaselineStore(db)
    store.initialize(RiskSessionBaseline("session-1", Decimal("100")))

    with pytest.raises(RiskSessionBaselineConflict, match="different"):
        store.initialize(RiskSessionBaseline("session-1", Decimal("101")))


def test_get_requires_initialized_session() -> None:
    store = PostgresRiskSessionBaselineStore(FakeDb())

    with pytest.raises(RiskSessionBaselineMissing, match="not initialized"):
        store.get("missing")


def test_baseline_rejects_blank_session_and_non_finite_value() -> None:
    with pytest.raises(ValueError, match="session id"):
        RiskSessionBaseline("   ", Decimal("0"))
    with pytest.raises(ValueError, match="finite"):
        RiskSessionBaseline("session-1", Decimal("NaN"))


def test_get_returns_durable_value() -> None:
    db = FakeDb({
        "session-1": {
            "session_id": "session-1",
            "daily_realized_pnl_baseline": "42.25",
        }
    })
    store = PostgresRiskSessionBaselineStore(db)

    assert store.get("session-1") == RiskSessionBaseline("session-1", Decimal("42.25"))
