"""Fail-closed post-fill broker state synchronization primitives."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Awaitable, Callable

from app.brokers.base import Account, BrokerPosition
from .gate import RiskSnapshot


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
    fills. The caller remains responsible for persisting the snapshot and for
    defining the daily-loss baseline used by RiskSnapshot.
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
    """Build the next deterministic risk snapshot from a fresh broker state.

    The daily-loss baseline is explicit; absolute broker lifetime realized P&L
    is never silently treated as today's P&L.
    """
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
