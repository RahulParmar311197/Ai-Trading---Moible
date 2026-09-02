from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol


class RiskSessionBaselineConflict(ValueError):
    """Raised when a session is re-initialized with a different baseline."""


class RiskSessionBaselineMissing(LookupError):
    """Raised when no authoritative baseline exists for a requested session."""


@dataclass(frozen=True)
class RiskSessionBaseline:
    """Explicit risk-session identity and its authoritative realized-P&L baseline."""

    session_id: str
    daily_realized_pnl_baseline: Decimal

    def __post_init__(self) -> None:
        if not self.session_id.strip():
            raise ValueError("risk session id must be non-empty")
        if not self.daily_realized_pnl_baseline.is_finite():
            raise ValueError("daily realized pnl baseline must be finite")


class RiskSessionBaselineStore(Protocol):
    """Persistence boundary for an externally-defined risk-session baseline."""

    def initialize(self, baseline: RiskSessionBaseline) -> RiskSessionBaseline: ...

    def get(self, session_id: str) -> RiskSessionBaseline: ...


class PostgresRiskSessionBaselineStore:
    """Durable PostgreSQL store; session boundaries remain an upstream responsibility."""

    def __init__(self, db: Any) -> None:
        self.db = db

    def initialize(self, baseline: RiskSessionBaseline) -> RiskSessionBaseline:
        row = self.db.execute_returning(
            """
            INSERT INTO risk_session_baselines (session_id, daily_realized_pnl_baseline)
            VALUES (:session_id, :daily_realized_pnl_baseline)
            ON CONFLICT (session_id) DO NOTHING
            RETURNING session_id, daily_realized_pnl_baseline
            """,
            {
                "session_id": baseline.session_id,
                "daily_realized_pnl_baseline": baseline.daily_realized_pnl_baseline,
            },
        )
        if row is not None:
            return _from_row(row)

        existing = self.db.fetch_one(
            """
            SELECT session_id, daily_realized_pnl_baseline
            FROM risk_session_baselines
            WHERE session_id = :session_id
            """,
            {"session_id": baseline.session_id},
        )
        if existing is None:
            raise RiskSessionBaselineMissing("risk session baseline disappeared during initialization")
        stored = _from_row(existing)
        if stored.daily_realized_pnl_baseline != baseline.daily_realized_pnl_baseline:
            raise RiskSessionBaselineConflict("risk session already has a different P&L baseline")
        return stored

    def get(self, session_id: str) -> RiskSessionBaseline:
        if not session_id.strip():
            raise ValueError("risk session id must be non-empty")
        row = self.db.fetch_one(
            """
            SELECT session_id, daily_realized_pnl_baseline
            FROM risk_session_baselines
            WHERE session_id = :session_id
            """,
            {"session_id": session_id},
        )
        if row is None:
            raise RiskSessionBaselineMissing("risk session baseline is not initialized")
        return _from_row(row)


def _from_row(row: Any) -> RiskSessionBaseline:
    return RiskSessionBaseline(
        session_id=str(row["session_id"]),
        daily_realized_pnl_baseline=Decimal(str(row["daily_realized_pnl_baseline"])),
    )
