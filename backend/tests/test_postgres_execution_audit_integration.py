"""PostgreSQL integration coverage for durable execution audit persistence."""

import os
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import text

from app.database.session import SQLAlchemyExecutor, create_database_engine
from app.execution import ExecutionAuditEvent, PostgresExecutionAuditRepository


@pytest.mark.integration
def test_execution_audit_repository_against_postgres() -> None:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not configured")

    root = Path(__file__).resolve().parents[2]
    engine = create_database_engine(database_url)
    with engine.begin() as connection:
        connection.exec_driver_sql(
            (root / "database/migrations/008_execution_audit.sql").read_text()
        )

    repository = PostgresExecutionAuditRepository(SQLAlchemyExecutor(engine))
    event = ExecutionAuditEvent(
        event_type="BROKER_CONFIRMED",
        client_order_id="integration-audit-order",
        reason="OPEN",
        timestamp=datetime(2026, 9, 2, 5, 30, tzinfo=timezone.utc),
    )

    repository.append(event)

    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                SELECT event_type, client_order_id, reason, occurred_at, payload
                FROM execution_audit_events
                WHERE client_order_id = :client_order_id
                ORDER BY id DESC
                LIMIT 1
                """
            ),
            {"client_order_id": event.client_order_id},
        ).mappings().one()
        connection.execute(
            text(
                "DELETE FROM execution_audit_events "
                "WHERE client_order_id = :client_order_id"
            ),
            {"client_order_id": event.client_order_id},
        )

    assert row["event_type"] == event.event_type
    assert row["client_order_id"] == event.client_order_id
    assert row["reason"] == event.reason
    assert row["occurred_at"] == event.timestamp
    assert row["payload"] == {
        "client_order_id": event.client_order_id,
        "event_type": event.event_type,
        "reason": event.reason,
        "timestamp": event.timestamp.isoformat(),
    }
    assert "token" not in row["payload"]
    assert "access_token" not in row["payload"]

    engine.dispose()
