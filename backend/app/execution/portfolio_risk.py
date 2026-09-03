from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from math import sqrt
from typing import Mapping, Sequence


class PortfolioRiskError(ValueError):
    """Raised when portfolio risk inputs cannot be evaluated safely."""


@dataclass(frozen=True)
class PortfolioPosition:
    symbol: str
    quantity: Decimal
    mark_price: Decimal
    realized_pnl: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")
    returns: tuple[Decimal, ...] = ()

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise PortfolioRiskError("portfolio position symbol is required")
        for name, value in (
            ("quantity", self.quantity),
            ("mark_price", self.mark_price),
            ("realized_pnl", self.realized_pnl),
            ("unrealized_pnl", self.unrealized_pnl),
        ):
            if not value.is_finite():
                raise PortfolioRiskError(f"portfolio {name} must be finite")
        if self.mark_price < 0:
            raise PortfolioRiskError("portfolio mark price cannot be negative")
        if any(not value.is_finite() for value in self.returns):
            raise PortfolioRiskError("portfolio returns must be finite")

    @property
    def notional(self) -> Decimal:
        return self.quantity * self.mark_price


@dataclass(frozen=True)
class PortfolioRiskLimits:
    max_gross_exposure: Decimal
    max_net_exposure: Decimal
    max_single_position_notional: Decimal
    max_pair_correlation: Decimal = Decimal("1")

    def __post_init__(self) -> None:
        for name, value in (
            ("max_gross_exposure", self.max_gross_exposure),
            ("max_net_exposure", self.max_net_exposure),
            ("max_single_position_notional", self.max_single_position_notional),
            ("max_pair_correlation", self.max_pair_correlation),
        ):
            if not value.is_finite():
                raise PortfolioRiskError(f"portfolio risk limit {name} must be finite")
            if value < 0:
                raise PortfolioRiskError(f"portfolio risk limit {name} cannot be negative")
        if self.max_pair_correlation > 1:
            raise PortfolioRiskError("max_pair_correlation cannot exceed 1")


@dataclass(frozen=True)
class PortfolioRiskAssessment:
    gross_exposure: Decimal
    net_exposure: Decimal
    total_realized_pnl: Decimal
    total_unrealized_pnl: Decimal
    single_position_notional: tuple[tuple[str, Decimal], ...]
    correlated_pairs: tuple[tuple[str, str, Decimal], ...]
    approved: bool
    reasons: tuple[str, ...]


def _pearson(left: Sequence[Decimal], right: Sequence[Decimal]) -> Decimal:
    if len(left) != len(right) or len(left) < 2:
        raise PortfolioRiskError("correlation requires equal return histories of at least two observations")
    left_mean = sum(left, Decimal("0")) / Decimal(len(left))
    right_mean = sum(right, Decimal("0")) / Decimal(len(right))
    covariance = sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right))
    left_var = sum((a - left_mean) ** 2 for a in left)
    right_var = sum((b - right_mean) ** 2 for b in right)
    if left_var == 0 or right_var == 0:
        raise PortfolioRiskError("correlation is undefined for constant return history")
    return covariance / Decimal(str(sqrt(float(left_var * right_var))))


def assess_portfolio(
    positions: Sequence[PortfolioPosition],
    limits: PortfolioRiskLimits,
) -> PortfolioRiskAssessment:
    """Compute portfolio exposure/correlation state without authorizing execution.

    This is deliberately a monitoring primitive. It has no broker or order
    mutation path; callers must apply its result through the deterministic
    execution risk gate.
    """
    symbols = [position.symbol for position in positions]
    if len(set(symbols)) != len(symbols):
        raise PortfolioRiskError("portfolio contains duplicate symbols")

    gross = sum((abs(position.notional) for position in positions), Decimal("0"))
    net = sum((position.notional for position in positions), Decimal("0"))
    realized = sum((position.realized_pnl for position in positions), Decimal("0"))
    unrealized = sum((position.unrealized_pnl for position in positions), Decimal("0"))
    if any(not value.is_finite() for value in (gross, net, realized, unrealized)):
        raise PortfolioRiskError("portfolio aggregate state is non-finite")

    single = tuple((position.symbol, abs(position.notional)) for position in positions)
    reasons: list[str] = []
    if gross > limits.max_gross_exposure:
        reasons.append("gross exposure limit exceeded")
    if abs(net) > limits.max_net_exposure:
        reasons.append("net exposure limit exceeded")
    for symbol, notional in single:
        if notional > limits.max_single_position_notional:
            reasons.append(f"single position exposure limit exceeded: {symbol}")

    correlated: list[tuple[str, str, Decimal]] = []
    for index, left in enumerate(positions):
        if not left.returns:
            continue
        for right in positions[index + 1 :]:
            if not right.returns:
                continue
            correlation = _pearson(left.returns, right.returns)
            if correlation >= limits.max_pair_correlation:
                correlated.append((left.symbol, right.symbol, correlation))
                if limits.max_pair_correlation < 1:
                    reasons.append(f"correlation concentration limit exceeded: {left.symbol}/{right.symbol}")

    return PortfolioRiskAssessment(
        gross_exposure=gross,
        net_exposure=net,
        total_realized_pnl=realized,
        total_unrealized_pnl=unrealized,
        single_position_notional=single,
        correlated_pairs=tuple(correlated),
        approved=not reasons,
        reasons=tuple(reasons),
    )
