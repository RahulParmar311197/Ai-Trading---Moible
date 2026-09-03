"""Durable application sink for the latest broker-derived execution risk state."""

from __future__ import annotations

from decimal import Decimal

from app.database.session import SQLAlchemyExecutor

from .gate import RiskSnapshot
from .state_sync import BrokerRiskState


class PostgresExecutionRiskStateSink:
    """Persist the latest risk state for an explicit trading session."""

    def __init__(self, executor: SQLAlchemyExecutor, *, session_id: str) -> None:
        if not session_id.strip():
            raise ValueError("session_id must not be blank")
        self._executor = executor
        self._session_id = session_id

    async def __call__(self, snapshot: RiskSnapshot, state: BrokerRiskState) -> None:
        self._executor.execute(
            """
            INSERT INTO execution_risk_state
                (session_id, balance, realized_pnl, position_quantity, halted, updated_at)
            VALUES
                (:session_id, :balance, :realized_pnl, :position_quantity, :halted, NOW())
            ON CONFLICT (session_id) DO UPDATE SET
                balance = EXCLUDED.balance,
                realized_pnl = EXCLUDED.realized_pnl,
                position_quantity = EXCLUDED.position_quantity,
                halted = EXCLUDED.halted,
                updated_at = NOW()
            """,
            {
                "session_id": self._session_id,
                "balance": Decimal(snapshot.balance),
                "realized_pnl": Decimal(snapshot.realized_pnl),
                "position_quantity": snapshot.position_quantity,
                "halted": snapshot.halted,
            },
        )
