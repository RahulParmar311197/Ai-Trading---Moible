from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.execution import autonomous
from app.execution.autonomous import AutonomousDecisionContext, AutonomousDecisionPipeline, DecisionCandidate
from app.execution.gate import DeterministicExecutionGate, RiskLimits, RiskSnapshot
from app.execution.portfolio_risk import PortfolioPosition, PortfolioRiskError, PortfolioRiskLimits


NOW = datetime(2026, 9, 3, 10, 0, tzinfo=timezone.utc)


def make_pipeline() -> AutonomousDecisionPipeline:
    return AutonomousDecisionPipeline(
        DeterministicExecutionGate(RiskLimits(max_order_notional=Decimal("100000"), max_position_quantity=10)),
        PortfolioRiskLimits(max_gross_exposure=Decimal("1000000"), max_net_exposure=Decimal("1000000"), max_single_position_notional=Decimal("100000")),
    )


def make_context(*, observed_at: datetime = NOW, halted: bool = False, positions: tuple[PortfolioPosition, ...] = ()) -> AutonomousDecisionContext:
    return AutonomousDecisionContext(
        session_id="session-1",
        observed_at=observed_at,
        now=NOW,
        max_state_age_seconds=30,
        risk_snapshot=RiskSnapshot(balance=Decimal("100000"), realized_pnl=Decimal("0"), halted=halted, position_quantity=0),
        positions=positions,
    )


def make_candidate(**kwargs) -> DecisionCandidate:
    values = dict(strategy_id="strategy-1", symbol="NIFTY", side="BUY", quantity=1, market_price=Decimal("100"), returns=(0.01, 0.02, 0.015))
    values.update(kwargs)
    return DecisionCandidate(**values)


def test_approved_candidate_produces_broker_neutral_intent() -> None:
    decision = make_pipeline().evaluate(make_candidate(generated_by_ai=True), make_context())

    assert decision.approved
    assert decision.intent is not None
    assert decision.intent.generated_by_ai is True
    assert decision.intent.symbol == "NIFTY"
    assert "broker submission remains separate" in decision.reason


def test_stale_authoritative_state_fails_closed() -> None:
    decision = make_pipeline().evaluate(make_candidate(), make_context(observed_at=NOW - timedelta(seconds=31)))

    assert not decision.approved
    assert decision.intent is None
    assert "stale" in decision.reason


def test_risk_halt_rejects_candidate() -> None:
    decision = make_pipeline().evaluate(make_candidate(), make_context(halted=True))

    assert not decision.approved
    assert decision.intent is None
    assert "risk rejected" in decision.reason


def test_missing_candidate_return_history_is_rejected() -> None:
    with pytest.raises(ValueError, match="return history"):
        make_candidate(returns=(0.01,))


def test_unsatisfied_strategy_conditions_are_rejected() -> None:
    with pytest.raises(ValueError, match="unsatisfied"):
        make_candidate(conditions_missing=("bullish_mss",))


def test_projected_portfolio_exposure_is_checked() -> None:
    pipeline = AutonomousDecisionPipeline(
        DeterministicExecutionGate(RiskLimits(max_order_notional=Decimal("100000"), max_position_quantity=20)),
        PortfolioRiskLimits(max_gross_exposure=Decimal("1000000"), max_net_exposure=Decimal("1000000"), max_single_position_notional=Decimal("100")),
    )
    decision = pipeline.evaluate(make_candidate(quantity=2, market_price=Decimal("100")), make_context())

    assert not decision.approved
    assert decision.intent is None
    assert "portfolio risk rejected" in decision.reason


def test_existing_position_is_projected_before_portfolio_check() -> None:
    position = PortfolioPosition(symbol="NIFTY", quantity=1, mark_price=Decimal("100"), returns=(0.01, 0.02, 0.015))
    pipeline = AutonomousDecisionPipeline(
        DeterministicExecutionGate(RiskLimits(max_order_notional=Decimal("100000"), max_position_quantity=20)),
        PortfolioRiskLimits(max_gross_exposure=Decimal("1000000"), max_net_exposure=Decimal("1000000"), max_single_position_notional=Decimal("150")),
    )
    decision = pipeline.evaluate(make_candidate(quantity=1), make_context(positions=(position,)))

    assert not decision.approved
    assert decision.intent is None
    assert "portfolio risk rejected" in decision.reason


def test_unexpected_portfolio_risk_error_is_propagated(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args, **kwargs):
        raise RuntimeError("programmer defect")

    monkeypatch.setattr(autonomous, "assess_portfolio", fail)

    with pytest.raises(RuntimeError, match="programmer defect"):
        make_pipeline().evaluate(make_candidate(), make_context())


def test_expected_portfolio_risk_error_fails_closed() -> None:
    def reject(*args, **kwargs):
        raise PortfolioRiskError("invalid portfolio state")

    # The domain-level risk error is intentionally converted to a deterministic rejection.
    # Unexpected exceptions remain visible so defects cannot be silently masked.
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(autonomous, "assess_portfolio", reject)
    try:
        decision = make_pipeline().evaluate(make_candidate(), make_context())
    finally:
        monkeypatch.undo()

    assert not decision.approved
    assert decision.intent is None
    assert "portfolio risk evaluation failed" in decision.reason
