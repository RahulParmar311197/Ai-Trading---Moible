"""Explicit trading-session lifecycle for deterministic risk accounting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .gate import RiskSnapshot
from .risk_session import (
    RiskSessionBaseline,
    RiskSessionBaselineMissing,
    RiskSessionBaselineStore,
)
from .state_sync import (
    BrokerRiskState,
    BrokerStateSynchronizer,
    risk_snapshot_from_persisted_session,
)


class TradingSessionError(RuntimeError):
    """Raised when an authoritative trading session cannot be established."""


class TradingSessionIdentityProvider(Protocol):
    """Upstream authority for session identity; this layer never invents it."""

    def current_session_id(self) -> str: ...


@dataclass(frozen=True)
class TradingSession:
    """Immutable session identity and broker baseline used by risk checks."""

    session_id: str
    baseline: RiskSessionBaseline
    state: BrokerRiskState


class TradingSessionLifecycle:
    """Establish and refresh a risk session without deriving market boundaries locally.

    Session identity is supplied by an authoritative upstream provider. The first
    broker refresh establishes a missing session baseline durably; once a baseline
    exists, startup/resume always reuses that persisted value even when broker
    realized P&L has changed since the previous process run.
    """

    def __init__(
        self,
        identity_provider: TradingSessionIdentityProvider,
        baseline_store: RiskSessionBaselineStore,
        state_synchronizer: BrokerStateSynchronizer,
    ) -> None:
        self._identity_provider = identity_provider
        self._baseline_store = baseline_store
        self._state_synchronizer = state_synchronizer

    async def establish(self) -> TradingSession:
        session_id = self._identity_provider.current_session_id().strip()
        if not session_id:
            raise TradingSessionError("authoritative trading session id is unavailable")

        try:
            baseline = self._baseline_store.get(session_id)
        except RiskSessionBaselineMissing:
            state = await self._refresh()
            baseline = RiskSessionBaseline(
                session_id=session_id,
                daily_realized_pnl_baseline=state.realized_pnl,
            )
            try:
                stored = self._baseline_store.initialize(baseline)
            except Exception as exc:
                raise TradingSessionError(
                    f"risk session baseline initialization failed: {type(exc).__name__}"
                ) from exc
            return TradingSession(session_id=session_id, baseline=stored, state=state)
        except Exception as exc:
            raise TradingSessionError(
                f"risk session baseline lookup failed: {type(exc).__name__}"
            ) from exc

        state = await self._refresh()
        return TradingSession(session_id=session_id, baseline=baseline, state=state)

    async def refresh(self, *, session_id: str) -> TradingSession:
        normalized = session_id.strip()
        if not normalized:
            raise TradingSessionError("trading session id must be non-empty")
        authoritative = self._identity_provider.current_session_id().strip()
        if not authoritative or authoritative != normalized:
            raise TradingSessionError("requested session does not match authoritative session")
        state = await self._refresh()
        try:
            baseline = self._baseline_store.get(normalized)
        except Exception as exc:
            raise TradingSessionError(
                f"risk session baseline lookup failed: {type(exc).__name__}"
            ) from exc
        return TradingSession(session_id=normalized, baseline=baseline, state=state)

    async def risk_snapshot(
        self,
        *,
        session_id: str,
        symbol: str,
        halted: bool = False,
    ) -> RiskSnapshot:
        session = await self.refresh(session_id=session_id)
        return risk_snapshot_from_persisted_session(
            session.state,
            baseline_store=self._baseline_store,
            session_id=session.session_id,
            symbol=symbol,
            halted=halted,
        )

    async def _refresh(self) -> BrokerRiskState:
        try:
            return await self._state_synchronizer.refresh()
        except Exception as exc:
            raise TradingSessionError(
                f"broker state refresh failed: {type(exc).__name__}"
            ) from exc
