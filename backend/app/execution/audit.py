from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Protocol

from .controlled import ExecutionAuditEvent


class ExecutionAuditRepository(Protocol):
    """Durable storage boundary for controlled-execution audit events."""

    def append(self, event: ExecutionAuditEvent) -> None: ...


class PostgresExecutionAuditRepository:
    """PostgreSQL implementation for the provider-neutral execution audit boundary."""

    def __init__(self, db: Any) -> None:
        self.db = db

    def append(self, event: ExecutionAuditEvent) -> None:
        self.db.execute(
            """
            INSERT INTO execution_audit_events
              (event_type, client_order_id, reason, occurred_at, payload)
            VALUES
              (:event_type, :client_order_id, :reason, :occurred_at, CAST(:payload AS JSONB))
            """,
            {
                "event_type": event.event_type,
                "client_order_id": event.client_order_id or None,
                "reason": event.reason,
                "occurred_at": event.timestamp,
                "payload": json.dumps(_safe_payload(event), sort_keys=True, separators=(",", ":")),
            },
        )


def _safe_payload(event: ExecutionAuditEvent) -> Mapping[str, str]:
    """Persist only non-secret execution facts; credentials never enter the audit payload."""
    return {
        "event_type": event.event_type,
        "client_order_id": event.client_order_id,
        "reason": event.reason,
        "timestamp": event.timestamp.isoformat(),
    }


class DurableExecutionAuditSink:
    """Callable adapter suitable for ControlledBrokerExecution.audit_sink."""

    def __init__(self, repository: ExecutionAuditRepository) -> None:
        self._repository = repository

    def __call__(self, event: ExecutionAuditEvent) -> None:
        self._repository.append(event)
