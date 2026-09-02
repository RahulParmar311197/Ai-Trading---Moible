"""Fail-closed broker state synchronization primitives."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Awaitable, Callable

from app.brokers.base import Account, BrokerPosition
from .gate import RiskSnapshot
from .risk_session import RiskSessionBaselineStore


class StateSynchronizationError(RuntimeError):
    """Raised when broker state cannot be safely synchronized."""


@dataclass(frozen=True)
class BrokerRiskState:
    """Immutable broker snapshot suitable for constructing the next risk state."""

    account: Account
    positions: tuple[BrokerPosition, ...]
    realized_pnl: Decimal
    unrealized_pnl: Decimal

    def __post_init__(self) -> None:
        if not self.realized_pnl.is_finite() or not self.unrealized_pnl.is_finite():
            raise ValueError("broker pnl values must be finite")


class BrokerStateSynchronizer:
    """Refresh account and positions from the broker before the next decision.

    P&L is aggregated from provider position records rather than invented from
    fills. The caller remains responsible for choosing the explicit risk-session
    identity; the persisted baseline is resolved separately.
    """

    def __init__(
        self,
        get_account: Callable[[], Awaitable[Account]],
        get_positions: Callable[[], Awaitable[tuple[BrokerPosition, ...]]],
    ) -> None:
        self._get_account = get_account
        self._get_positions = get_positions

    async def refresh(self) -> BrokerRiskState:
        try:
            account = await self._get_account()
            positions = await self._get_positions()
        except Exception as exc:
            raise StateSynchronizationError(
                f"broker state refresh failed: {type(exc).__name__}"
            ) from exc

        if not isinstance(account, Account):
            raise StateSynchronizationError("broker returned invalid account state")
        if not isinstance(positions, tuple) or any(
            not isinstance(position, BrokerPosition) for position in positions
        ):
            raise StateSynchronizationError("broker returned invalid position state")

        realized_pnl = sum((position.realized_pnl for position in positions), Decimal("0"))
        unrealized_pnl = sum((position.unrealized_pnl for position in positions), Decimal("0"))
        if not realized_pnl.is_finite() or not unrealized_pnl.is_finite():
            raise StateSynchronizationError("broker returned non-finite pnl state")

        return BrokerRiskState(
            account=account,
            positions=positions,
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
        )


def risk_snapshot_from_broker_state(
    state: BrokerRiskState,
    *,
    symbol: str,
    daily_realized_pnl_baseline: Decimal,
    halted: bool = False,
) -> RiskSnapshot:
    """Build a deterministic risk snapshot from fresh broker state."""
    if not daily_realized_pnl_baseline.is_finite():
        raise StateSynchronizationError("daily realized pnl baseline must be finite")
    position_quantity = sum(
        position.quantity for position in state.positions if position.symbol == symbol
    )
    daily_realized_pnl = state.realized_pnl - daily_realized_pnl_baseline
    if not daily_realized_pnl.is_finite():
        raise StateSynchronizationError("derived daily realized pnl must be finite")
    return RiskSnapshot(
        balance=state.account.balance,
        realized_pnl=daily_realized_pnl,
        halted=halted,
        position_quantity=position_quantity,
    )


def risk_snapshot_from_persisted_session(
    state: BrokerRiskState,
    *,
    baseline_store: RiskSessionBaselineStore,
    session_id: str,
    symbol: str,
    halted: bool = False,
) -> RiskSnapshot:
    """Build risk state only from a persisted, explicitly identified session.

    Missing or conflicting session state is never replaced with a wall-clock
    default or broker lifetime P&L value.
    """
    try:
        baseline = baseline_store.get(session_id)
    except Exception as exc:
        raise StateSynchronizationError(
            f"risk session baseline lookup failed: {type(exc).__name__}"
        ) from exc
    return risk_snapshot_from_broker_state(
        state,
        symbol=symbol,
        daily_realized_pnl_baseline=baseline.daily_realized_pnl_baseline,
        halted=halted,
    )
