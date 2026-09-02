"""Fail-closed post-fill account state synchronization primitives."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from math import isfinite
from typing import Callable, Iterable

from app.brokers.base import Account, BrokerPosition


class StateSynchronizationError(RuntimeError):
    """Raised when broker state cannot be safely synchronized."""


@dataclass(frozen=True)
class AccountRiskState:
    """Authoritative account/risk values captured from a broker snapshot."""

    balance: Decimal
    available_margin: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal

    def __post_init__(self) -> None:
        values = (
            self.balance,
            self.available_margin,
            self.realized_pnl,
            self.unrealized_pnl,
        )
        if any(not value.is_finite() for value in values):
            raise ValueError("account risk state values must be finite")


class BrokerStateSynchronizer:
    """Refresh account and position state atomically from broker boundaries.

    This component intentionally does not derive realized/unrealized P&L locally.
    The broker is the source of truth for account-level financial state; callers
    must persist the returned snapshot before permitting a subsequent live order.
    """

    def __init__(
        self,
        get_account: Callable[[], Account],
        get_positions: Callable[[], Iterable[BrokerPosition]],
    ) -> None:
        self._get_account = get_account
        self._get_positions = get_positions

    def refresh(self) -> tuple[AccountRiskState, tuple[BrokerPosition, ...]]:
        try:
            account = self._get_account()
            positions = tuple(self._get_positions())
        except Exception as exc:
            raise StateSynchronizationError(
                f"broker state refresh failed: {type(exc).__name__}"
            ) from exc

        if not isinstance(account, Account):
            raise StateSynchronizationError("broker returned invalid account state")
        if any(not isinstance(position, BrokerPosition) for position in positions):
            raise StateSynchronizationError("broker returned invalid position state")

        financial_values = (
            account.balance,
            account.available_margin,
            account.realized_pnl,
            account.unrealized_pnl,
        )
        if any(not value.is_finite() for value in financial_values):
            raise StateSynchronizationError("broker returned non-finite account state")

        return (
            AccountRiskState(
                balance=account.balance,
                available_margin=account.available_margin,
                realized_pnl=account.realized_pnl,
                unrealized_pnl=account.unrealized_pnl,
            ),
            positions,
        )
