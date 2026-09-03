from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.database.session import SQLAlchemyExecutor


class EmergencyControlError(RuntimeError):
    """Raised when durable emergency-control state cannot be trusted."""


@dataclass(frozen=True)
class EmergencyControlState:
    active: bool
    reason: str
    updated_at: datetime


class EmergencyControlStore(Protocol):
    def get_state(self) -> EmergencyControlState: ...

    def set_active(self, active: bool, reason: str) -> EmergencyControlState: ...


class PostgresEmergencyControlStore:
    """Durable singleton emergency-stop state; database failures fail closed."""

    def __init__(self, executor: SQLAlchemyExecutor) -> None:
        self._executor = executor

    def get_state(self) -> EmergencyControlState:
        try:
            row = self._executor.fetch_one(
                """
                SELECT active, reason, updated_at
                FROM execution_emergency_control
                WHERE control_id = 1
                """,
                {},
            )
        except Exception as exc:
            raise EmergencyControlError("emergency control state unavailable") from exc
        if row is None or not isinstance(row.get("active"), bool):
            raise EmergencyControlError("emergency control state is missing or invalid")
        reason = row.get("reason")
        updated_at = row.get("updated_at")
        if not isinstance(reason, str) or not reason.strip() or not isinstance(updated_at, datetime):
            raise EmergencyControlError("emergency control state is incomplete")
        return EmergencyControlState(row["active"], reason, updated_at)

    def set_active(self, active: bool, reason: str) -> EmergencyControlState:
        if not isinstance(active, bool):
            raise EmergencyControlError("emergency control active state must be boolean")
        if not isinstance(reason, str) or not reason.strip():
            raise EmergencyControlError("emergency control reason must be non-empty")
        try:
            row = self._executor.execute_returning(
                """
                INSERT INTO execution_emergency_control (control_id, active, reason, updated_at)
                VALUES (1, :active, :reason, NOW())
                ON CONFLICT (control_id) DO UPDATE SET
                    active = EXCLUDED.active,
                    reason = EXCLUDED.reason,
                    updated_at = EXCLUDED.updated_at
                RETURNING active, reason, updated_at
                """,
                {"active": active, "reason": reason.strip()},
            )
        except Exception as exc:
            raise EmergencyControlError("emergency control state could not be persisted") from exc
        if row is None or not isinstance(row.get("active"), bool):
            raise EmergencyControlError("emergency control persistence returned invalid state")
        updated_at = row.get("updated_at")
        persisted_reason = row.get("reason")
        if not isinstance(updated_at, datetime) or not isinstance(persisted_reason, str) or not persisted_reason.strip():
            raise EmergencyControlError("emergency control persistence returned incomplete state")
        return EmergencyControlState(row["active"], persisted_reason, updated_at)
