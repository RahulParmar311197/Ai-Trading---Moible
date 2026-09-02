from decimal import Decimal

import pytest

from app.brokers.base import Account, BrokerPosition
from app.execution.state_sync import (
    BrokerRiskState,
    BrokerStateSynchronizer,
    StateSynchronizationError,
    risk_snapshot_from_broker_state,
)


@pytest.mark.asyncio
async def test_refresh_returns_fresh_positions_and_aggregated_pnl() -> None:
    account = Account(
        account_id="paper",
        balance=Decimal("100000"),
        available_margin=Decimal("80000"),
    )
    positions = (
        BrokerPosition(
            symbol="NIFTY",
            quantity=10,
            average_price=Decimal("100"),
            realized_pnl=Decimal("25"),
            unrealized_pnl=Decimal("-5"),
        ),
        BrokerPosition(
            symbol="BANKNIFTY",
            quantity=-2,
            average_price=Decimal("200"),
            realized_pnl=Decimal("10"),
            unrealized_pnl=Decimal("7"),
        ),
    )

    async def get_account() -> Account:
        return account

    async def get_positions() -> tuple[BrokerPosition, ...]:
        return positions

    state = await BrokerStateSynchronizer(get_account, get_positions).refresh()

    assert state.account == account
    assert state.positions == positions
    assert state.realized_pnl == Decimal("35")
    assert state.unrealized_pnl == Decimal("2")


def test_risk_snapshot_uses_explicit_daily_realized_pnl_baseline() -> None:
    account = Account(
        account_id="paper",
        balance=Decimal("100000"),
        available_margin=Decimal("80000"),
    )
    state = BrokerRiskState(
        account=account,
        positions=(
            BrokerPosition(
                symbol="NIFTY",
                quantity=7,
                average_price=Decimal("100"),
                realized_pnl=Decimal("25"),
            ),
        ),
        realized_pnl=Decimal("25"),
        unrealized_pnl=Decimal("-3"),
    )

    snapshot = risk_snapshot_from_broker_state(
        state,
        symbol="NIFTY",
        daily_realized_pnl_baseline=Decimal("40"),
    )

    assert snapshot.balance == Decimal("100000")
    assert snapshot.position_quantity == 7
    assert snapshot.realized_pnl == Decimal("-15")
    assert not snapshot.halted


def test_risk_snapshot_rejects_non_finite_daily_baseline() -> None:
    account = Account(
        account_id="paper",
        balance=Decimal("100000"),
        available_margin=Decimal("80000"),
    )
    state = BrokerRiskState(
        account=account,
        positions=(),
        realized_pnl=Decimal("0"),
        unrealized_pnl=Decimal("0"),
    )

    with pytest.raises(StateSynchronizationError, match="baseline"):
        risk_snapshot_from_broker_state(
            state,
            symbol="NIFTY",
            daily_realized_pnl_baseline=Decimal("NaN"),
        )


@pytest.mark.asyncio
async def test_refresh_fails_closed_on_broker_exception() -> None:
    async def get_account() -> Account:
        raise TimeoutError("provider timeout")

    async def get_positions() -> tuple[BrokerPosition, ...]:
        return ()

    with pytest.raises(StateSynchronizationError, match="TimeoutError"):
        await BrokerStateSynchronizer(get_account, get_positions).refresh()


@pytest.mark.asyncio
async def test_refresh_rejects_malformed_position_response() -> None:
    async def get_account() -> Account:
        return Account(
            account_id="paper",
            balance=Decimal("100000"),
            available_margin=Decimal("80000"),
        )

    async def get_positions() -> tuple[BrokerPosition, ...]:
        return ("not-a-position",)  # type: ignore[return-value]

    with pytest.raises(StateSynchronizationError, match="invalid position state"):
        await BrokerStateSynchronizer(get_account, get_positions).refresh()
