from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence


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
        try:
            quantity = Decimal(str(self.quantity))
            mark_price = Decimal(str(self.mark_price))
            realized_pnl = Decimal(str(self.realized_pnl))
            unrealized_pnl = Decimal(str(self.unrealized_pnl))
            returns = tuple(Decimal(str(value)) for value in self.returns)
        except (ArithmeticError, ValueError, TypeError) as exc:
            raise PortfolioRiskError("portfolio financial values must be numeric") from exc
        for name, value in (("quantity", quantity), ("mark_price", mark_price), ("realized_pnl", realized_pnl), ("unrealized_pnl", unrealized_pnl)):
            if not value.is_finite():
                raise PortfolioRiskError(f"portfolio {name} must be finite")
        if mark_price < 0:
            raise PortfolioRiskError("portfolio mark price cannot be negative")
        if any(not value.is_finite() for value in returns):
            raise PortfolioRiskError("portfolio returns must be finite")
        object.__setattr__(self, "quantity", quantity)
        object.__setattr__(self, "mark_price", mark_price)
        object.__setattr__(self, "realized_pnl", realized_pnl)
        object.__setattr__(self, "unrealized_pnl", unrealized_pnl)
        object.__setattr__(self, "returns", returns)

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
        try:
            values = {
                "max_gross_exposure": Decimal(str(self.max_gross_exposure)),
                "max_net_exposure": Decimal(str(self.max_net_exposure)),
                "max_single_position_notional": Decimal(str(self.max_single_position_notional)),
                "max_pair_correlation": Decimal(str(self.max_pair_correlation)),
            }
        except (ArithmeticError, ValueError, TypeError) as exc:
            raise PortfolioRiskError("portfolio risk limits must be numeric") from exc
        for name, value in values.items():
            if not value.is_finite():
                raise PortfolioRiskError(f"portfolio risk limit {name} must be finite")
            if value < 0:
                raise PortfolioRiskError(f"portfolio risk limit {name} cannot be negative")
        if values["max_pair_correlation"] > 1:
            raise PortfolioRiskError("max_pair_correlation cannot exceed 1")
        for name, value in values.items():
            object.__setattr__(self, name, value)


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
    denominator = left_var * right_var
    if denominator <= 0:
        raise PortfolioRiskError("correlation is undefined for constant return history")
    return covariance / Decimal(str(denominator.sqrt()))


def assess_portfolio(positions: Sequence[PortfolioPosition], limits: PortfolioRiskLimits) -> PortfolioRiskAssessment:
    """Compute portfolio exposure/correlation state without authorizing execution."""
    if not isinstance(positions, Sequence):
        raise PortfolioRiskError("portfolio positions must be a sequence")
    if not isinstance(limits, PortfolioRiskLimits):
        raise PortfolioRiskError("portfolio risk limits are required")
    if any(not isinstance(position, PortfolioPosition) for position in positions):
        raise PortfolioRiskError("portfolio contains invalid position state")
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
    return PortfolioRiskAssessment(gross, net, realized, unrealized, single, tuple(correlated), not reasons, tuple(reasons))
