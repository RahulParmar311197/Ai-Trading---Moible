from datetime import datetime, timezone
import json

from app.execution import DurableExecutionAuditSink, ExecutionAuditEvent, PostgresExecutionAuditRepository


class FakeDb:
    def __init__(self) -> None:
        self.calls = []

    def execute(self, sql, params) -> None:
        self.calls.append((sql, params))


def event() -> ExecutionAuditEvent:
    return ExecutionAuditEvent(
        event_type="BROKER_CONFIRMED",
        client_order_id="client-1",
        reason="OPEN",
        timestamp=datetime(2026, 9, 2, 5, 30, tzinfo=timezone.utc),
    )


def test_postgres_execution_audit_repository_persists_only_safe_facts() -> None:
    db = FakeDb()
    repository = PostgresExecutionAuditRepository(db)
    repository.append(event())

    sql, params = db.calls[0]
    assert "execution_audit_events" in sql
    assert params["event_type"] == "BROKER_CONFIRMED"
    assert params["client_order_id"] == "client-1"
    assert params["reason"] == "OPEN"
    payload = json.loads(params["payload"])
    assert payload == {
        "client_order_id": "client-1",
        "event_type": "BROKER_CONFIRMED",
        "reason": "OPEN",
        "timestamp": "2026-09-02T05:30:00+00:00",
    }
    assert "token" not in payload
    assert "access_token" not in payload


def test_durable_sink_adapts_repository_to_controlled_execution_callback() -> None:
    captured = []

    class Repository:
        def append(self, audit_event) -> None:
            captured.append(audit_event)

    sink = DurableExecutionAuditSink(Repository())
    audit_event = event()
    sink(audit_event)
    assert captured == [audit_event]
