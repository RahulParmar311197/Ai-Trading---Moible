from decimal import Decimal

import pytest

from app.brokers.base import Account, BrokerPosition
from app.execution.risk_session import RiskSessionBaseline, RiskSessionBaselineConflict
from app.execution.session_lifecycle import TradingSessionError, TradingSessionLifecycle
from app.execution.state_sync import BrokerStateSynchronizer


class Identity:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id

    def current_session_id(self) -> str:
        return self.session_id


class Store:
    def __init__(self) -> None:
        self.values: dict[str, RiskSessionBaseline] = {}

    def initialize(self, baseline: RiskSessionBaseline) -> RiskSessionBaseline:
        existing = self.values.get(baseline.session_id)
        if existing is not None:
            if existing.daily_realized_pnl_baseline != baseline.daily_realized_pnl_baseline:
                raise RiskSessionBaselineConflict("different baseline")
            return existing
        self.values[baseline.session_id] = baseline
        return baseline

    def get(self, session_id: str) -> RiskSessionBaseline:
        return self.values[session_id]


@pytest.mark.asyncio
async def test_establish_persists_first_broker_realized_pnl_as_session_baseline() -> None:
    identity = Identity("session-2026-09-03")
    store = Store()
    state = BrokerStateSynchronizer(
        _async_account,
        lambda: _async_positions(realized=Decimal("1250")),
    )
    lifecycle = TradingSessionLifecycle(identity, store, state)

    session = await lifecycle.establish()

    assert session.session_id == "session-2026-09-03"
    assert session.baseline.daily_realized_pnl_baseline == Decimal("1250")
    assert store.values["session-2026-09-03"] == session.baseline


@pytest.mark.asyncio
async def test_refresh_rejects_non_authoritative_session() -> None:
    lifecycle = TradingSessionLifecycle(
        Identity("authoritative"),
        Store(),
        BrokerStateSynchronizer(_async_account, _async_positions),
    )

    with pytest.raises(TradingSessionError, match="does not match authoritative"):
        await lifecycle.refresh(session_id="other")


@pytest.mark.asyncio
async def test_risk_snapshot_uses_persisted_baseline_not_current_realized_pnl() -> None:
    identity = Identity("session-1")
    store = Store()
    state = BrokerStateSynchronizer(
        _async_account,
        lambda: _async_positions(realized=Decimal("1250")),
    )
    lifecycle = TradingSessionLifecycle(identity, store, state)
    await lifecycle.establish()

    snapshot = await lifecycle.risk_snapshot(session_id="session-1", symbol="NSE_EQ|TEST")

    assert snapshot.realized_pnl == Decimal("0")


def _account(balance: int) -> Account:
    return Account(
        account_id="account-1",
        balance=Decimal(balance),
        available_margin=Decimal(balance),
    )


async def _async_account() -> Account:
    return _account(100_000)


async def _async_positions(*, realized: Decimal = Decimal("0")) -> tuple[BrokerPosition, ...]:
    return _positions(realized=realized)


def _positions(*, realized: Decimal = Decimal("0")) -> tuple[BrokerPosition, ...]:
    return (
        BrokerPosition(
            symbol="NSE_EQ|TEST",
            quantity=10,
            average_price=Decimal("100"),
            realized_pnl=realized,
        ),
    )
