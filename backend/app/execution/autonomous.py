from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from math import isfinite
from typing import Mapping, Sequence

from .gate import DeterministicExecutionGate, ExecutionDecision, RiskSnapshot
from .portfolio_risk import PortfolioPosition, PortfolioRiskAssessment, PortfolioRiskLimits, assess_portfolio


class AutonomousDecisionError(RuntimeError):
    """Raised when an autonomous decision cannot be evaluated safely."""


@dataclass(frozen=True)
class DecisionCandidate:
    """Structured strategy output; it contains no broker credentials or commands."""

    strategy_id: str
    symbol: str
    side: str
    quantity: int
    market_price: Decimal
    generated_by_ai: bool = False
    conditions_satisfied: tuple[str, ...] = ()
    conditions_missing: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.strategy_id.strip():
            raise ValueError("strategy id must be non-empty")
        if not self.symbol.strip():
            raise ValueError("symbol must be non-empty")
        if self.side.upper() not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if not self.market_price.is_finite() or self.market_price <= 0:
            raise ValueError("market price must be finite and positive")
        if self.conditions_missing:
            raise ValueError("candidate contains unsatisfied conditions")


@dataclass(frozen=True)
class AutonomousDecisionContext:
    """Authoritative state snapshot supplied to the deterministic pipeline."""

    session_id: str
    observed_at: datetime
    now: datetime
    max_state_age_seconds: float
    risk_snapshot: RiskSnapshot
    positions: tuple[PortfolioPosition, ...]

    def __post_init__(self) -> None:
        if not self.session_id.strip():
            raise ValueError("session id must be non-empty")
        if self.observed_at.tzinfo is None or self.now.tzinfo is None:
            raise ValueError("decision timestamps must be timezone-aware")
        if not isfinite(self.max_state_age_seconds) or self.max_state_age_seconds <= 0:
            raise ValueError("max state age must be finite and positive")
        if self.now < self.observed_at:
            raise ValueError("decision clock cannot precede observed state")


@dataclass(frozen=True)
class ExecutionIntent:
    """Deterministic, broker-neutral intent. This is not an order authorization."""

    session_id: str
    strategy_id: str
    symbol: str
    side: str
    quantity: int
    market_price: Decimal
    risk_decision: ExecutionDecision
    portfolio_risk: PortfolioRiskAssessment
    generated_by_ai: bool


@dataclass(frozen=True)
class AutonomousDecision:
    approved: bool
    reason: str
    intent: ExecutionIntent | None


class AutonomousDecisionPipeline:
    """Turns validated strategy candidates into broker-neutral intents only.

    This component never calls a broker and cannot activate live execution. Any
    eventual order must independently pass the controlled execution boundary.
    """

    def __init__(
        self,
        execution_gate: DeterministicExecutionGate,
        portfolio_limits: PortfolioRiskLimits,
    ) -> None:
        self._execution_gate = execution_gate
        self._portfolio_limits = portfolio_limits

    def evaluate(
        self,
        candidate: DecisionCandidate,
        context: AutonomousDecisionContext,
    ) -> AutonomousDecision:
        age = (context.now - context.observed_at).total_seconds()
        if age > context.max_state_age_seconds:
            return AutonomousDecision(False, "authoritative decision state is stale", None)

        if candidate.symbol not in {position.symbol for position in context.positions} and context.positions:
            positions = context.positions + (
                PortfolioPosition(
                    symbol=candidate.symbol,
                    quantity=0,
                    mark_price=candidate.market_price,
                    returns=(0.0, 0.0),
                ),
            )
        else:
            positions = context.positions

        try:
            portfolio = assess_portfolio(positions, self._portfolio_limits)
        except Exception as exc:
            return AutonomousDecision(False, f"portfolio risk evaluation failed: {type(exc).__name__}", None)
        if not portfolio.approved:
            return AutonomousDecision(False, "portfolio risk rejected candidate: " + "; ".join(portfolio.reasons), None)

        gate = self._execution_gate.evaluate(candidate, candidate.market_price, context.risk_snapshot)
        if not gate.approved:
            return AutonomousDecision(False, "execution risk rejected candidate: " + gate.reason, None)

        intent = ExecutionIntent(
            session_id=context.session_id,
            strategy_id=candidate.strategy_id,
            symbol=candidate.symbol,
            side=candidate.side.upper(),
            quantity=candidate.quantity,
            market_price=candidate.market_price,
            risk_decision=gate,
            portfolio_risk=portfolio,
            generated_by_ai=candidate.generated_by_ai,
        )
        return AutonomousDecision(True, "approved deterministic intent; broker submission remains separate", intent)
