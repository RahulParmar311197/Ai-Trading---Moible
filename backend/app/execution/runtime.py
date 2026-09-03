"""Fail-closed application composition for controlled broker execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.brokers.base import Broker
from app.brokers.durable_idempotency import PostgresBrokerIdempotencyStore
from app.database.session import SQLAlchemyExecutor, create_database_engine

from .audit import DurableExecutionAuditSink, PostgresExecutionAuditRepository
from .controlled import ControlledBrokerExecution
from .gate import DeterministicExecutionGate, RiskLimits
from .post_fill_sync import PostFillBrokerStateSynchronizer
from .risk_session import PostgresRiskSessionBaselineStore
from .session_lifecycle import TradingSessionIdentityProvider, TradingSessionLifecycle
from .state_sync import BrokerStateSynchronizer


@dataclass(frozen=True)
class ExecutionRuntime:
    """Fully composed execution dependencies; construction does not activate trading."""

    executor: ControlledBrokerExecution
    sessions: TradingSessionLifecycle


class StaticTradingSessionIdentityProvider:
    """Application boundary for an externally supplied session identifier."""

    def __init__(self, session_id: str) -> None:
        self._session_id = session_id

    def current_session_id(self) -> str:
        return self._session_id


def build_execution_runtime(
    broker: Broker,
    *,
    session_identity_provider: TradingSessionIdentityProvider,
    risk_limits: RiskLimits,
    confirmation_phrase: str,
    risk_state_sink: Callable,
    database_url: str | None = None,
) -> ExecutionRuntime:
    """Compose durable execution controls without authenticating or activating them."""
    engine = create_database_engine(database_url)
    db = SQLAlchemyExecutor(engine)
    baseline_store = PostgresRiskSessionBaselineStore(db)
    audit_repository = PostgresExecutionAuditRepository(db)
    idempotency_store = PostgresBrokerIdempotencyStore(db)
    broker_state = BrokerStateSynchronizer(broker.get_account, broker.get_positions)
    sessions = TradingSessionLifecycle(
        session_identity_provider,
        baseline_store,
        broker_state,
    )
    post_fill_sync = PostFillBrokerStateSynchronizer(
        broker_state=broker_state,
        baseline_store=baseline_store,
        session_id=session_identity_provider.current_session_id(),
        sink=risk_state_sink,
    )
    executor = ControlledBrokerExecution(
        broker,
        DeterministicExecutionGate(risk_limits),
        confirmation_phrase=confirmation_phrase,
        audit_sink=DurableExecutionAuditSink(audit_repository),
        idempotency_store=idempotency_store,
        post_fill_state_sync=post_fill_sync,
    )
    return ExecutionRuntime(executor=executor, sessions=sessions)
