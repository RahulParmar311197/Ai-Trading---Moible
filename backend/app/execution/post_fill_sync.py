"""Concrete fail-closed post-fill broker-state synchronization."""

from __future__ import annotations

from typing import Awaitable, Callable

from app.brokers.base import BrokerOrder
from .gate import RiskSnapshot
from .risk_session import RiskSessionBaselineStore
from .state_sync import (
    BrokerRiskState,
    BrokerStateSynchronizer,
    StateSynchronizationError,
    risk_snapshot_from_persisted_session,
)


RiskSnapshotSink = Callable[[RiskSnapshot, BrokerRiskState], Awaitable[None]]


class PostFillBrokerStateSynchronizer:
    """Refresh broker state after a mutation and persist the derived risk state.

    The session ID and baseline store are explicit dependencies. This class never
    invents a trading day, initializes a baseline, or derives P&L from the fill.
    The durable/application sink is also explicit so a successful refresh cannot
    be mistaken for durable lifecycle propagation unless the sink succeeds.
    """

    def __init__(
        self,
        *,
        broker_state: BrokerStateSynchronizer,
        baseline_store: RiskSessionBaselineStore,
        session_id: str,
        sink: RiskSnapshotSink,
    ) -> None:
        if not session_id.strip():
            raise ValueError("session_id must not be blank")
        self._broker_state = broker_state
        self._baseline_store = baseline_store
        self._session_id = session_id
        self._sink = sink

    async def synchronize(self, order: BrokerOrder) -> RiskSnapshot:
        try:
            state = await self._broker_state.refresh()
            snapshot = risk_snapshot_from_persisted_session(
                state,
                baseline_store=self._baseline_store,
                session_id=self._session_id,
                symbol=order.symbol,
            )
            await self._sink(snapshot, state)
            return snapshot
        except StateSynchronizationError:
            raise
        except Exception as exc:
            raise StateSynchronizationError(
                f"post-fill state propagation failed: {type(exc).__name__}"
            ) from exc

    async def __call__(self, order: BrokerOrder) -> None:
        await self.synchronize(order)
