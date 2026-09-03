from decimal import Decimal

import pytest

from app.brokers.base import BrokerOrder
from app.execution.autonomous import ExecutionIntent
from app.execution.autonomous_execution import AutonomousExecutionBridgeError, submit_autonomous_intent
from app.execution.gate import ExecutionDecision, RiskSnapshot
from app.execution.portfolio_risk import PortfolioRiskAssessment


def approved_intent(*, portfolio_approved: bool = True) -> ExecutionIntent:
    portfolio = PortfolioRiskAssessment(
        gross_exposure=Decimal("100"),
        net_exposure=Decimal("100"),
        total_realized_pnl=Decimal("0"),
        total_unrealized_pnl=Decimal("0"),
        single_position_notional=(("NIFTY", Decimal("100")),),
        correlated_pairs=(),
        approved=portfolio_approved,
        reasons=() if portfolio_approved else ("risk limit",),
    )
    return ExecutionIntent(
        session_id="session-1",
        strategy_id="strategy-1",
        symbol="NIFTY",
        side="BUY",
        quantity=1,
        market_price=Decimal("100"),
        risk_decision=ExecutionDecision(approved=True, reason="approved"),
        portfolio_risk=portfolio,
        generated_by_ai=True,
    )


class RecordingExecutor:
    def __init__(self) -> None:
        self.calls: list[tuple[BrokerOrder, Decimal, RiskSnapshot]] = []

    async def submit(self, order: BrokerOrder, *, market_price: Decimal, snapshot: RiskSnapshot) -> BrokerOrder:
        self.calls.append((order, market_price, snapshot))
        return order


@pytest.mark.asyncio
async def test_approved_intent_delegates_once_without_activation() -> None:
    executor = RecordingExecutor()
    snapshot = RiskSnapshot(balance=Decimal("100000"), realized_pnl=Decimal("0"), halted=False)

    result = await submit_autonomous_intent(
        executor,
        approved_intent(),
        client_order_id="auto-bridge-1",
        snapshot=snapshot,
    )

    assert result.client_order_id == "auto-bridge-1"
    assert len(executor.calls) == 1
    order, market_price, supplied_snapshot = executor.calls[0]
    assert order.average_price is None
    assert market_price == Decimal("100")
    assert supplied_snapshot is snapshot
    assert not hasattr(executor, "activate")


@pytest.mark.asyncio
async def test_portfolio_rejected_intent_never_reaches_controlled_executor() -> None:
    executor = RecordingExecutor()
    snapshot = RiskSnapshot(balance=Decimal("100000"), realized_pnl=Decimal("0"), halted=False)

    with pytest.raises(AutonomousExecutionBridgeError, match="portfolio-risk-approved"):
        await submit_autonomous_intent(
            executor,
            approved_intent(portfolio_approved=False),
            client_order_id="auto-bridge-2",
            snapshot=snapshot,
        )

    assert executor.calls == []


@pytest.mark.asyncio
async def test_controlled_executor_rejection_is_propagated() -> None:
    class RejectingExecutor(RecordingExecutor):
        async def submit(self, order: BrokerOrder, *, market_price: Decimal, snapshot: RiskSnapshot) -> BrokerOrder:
            raise RuntimeError("controlled boundary rejected")

    executor = RejectingExecutor()
    snapshot = RiskSnapshot(balance=Decimal("100000"), realized_pnl=Decimal("0"), halted=False)

    with pytest.raises(RuntimeError, match="controlled boundary rejected"):
        await submit_autonomous_intent(
            executor,
            approved_intent(),
            client_order_id="auto-bridge-3",
            snapshot=snapshot,
        )
