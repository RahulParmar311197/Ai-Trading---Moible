from decimal import Decimal
import os
from pathlib import Path

import pytest
from sqlalchemy import text

from app.database.session import SQLAlchemyExecutor, create_database_engine
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


@pytest.mark.integration
def test_postgres_risk_session_baseline_survives_store_recreation() -> None:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not configured")

    root = Path(__file__).resolve().parents[2]
    migration = root / "database/migrations/010_risk_session_baselines.sql"
    engine = create_database_engine(database_url)
    session_id = "integration-risk-session-baseline"
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(migration.read_text())
            connection.execute(
                text("DELETE FROM risk_session_baselines WHERE session_id = :session_id"),
                {"session_id": session_id},
            )

        baseline = RiskSessionBaseline(session_id, Decimal("1234.50"))
        first_store = PostgresRiskSessionBaselineStore(SQLAlchemyExecutor(engine))
        assert first_store.initialize(baseline) == baseline

        second_store = PostgresRiskSessionBaselineStore(SQLAlchemyExecutor(engine))
        assert second_store.get(session_id) == baseline
        assert second_store.initialize(baseline) == baseline

        with pytest.raises(RiskSessionBaselineConflict, match="different"):
            second_store.initialize(RiskSessionBaseline(session_id, Decimal("1235.50")))
    finally:
        with engine.begin() as connection:
            connection.execute(
                text("DELETE FROM risk_session_baselines WHERE session_id = :session_id"),
                {"session_id": session_id},
            )
        engine.dispose()
