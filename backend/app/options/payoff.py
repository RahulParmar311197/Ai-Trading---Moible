from __future__ import annotations

from decimal import Decimal, getcontext

from .models import OptionLeg, OptionPayoffReport, OptionType

getcontext().prec = 28

_ZERO = Decimal("0")
_ONE = Decimal("1")


def _intrinsic(leg: OptionLeg, underlying: Decimal) -> Decimal:
    contract = leg.contract
    if contract.option_type is OptionType.CALL:
        value = max(underlying - contract.strike, _ZERO)
    else:
        value = max(contract.strike - underlying, _ZERO)
    return value * Decimal(leg.quantity) * Decimal(getattr(contract, "lot_size", 1))


def payoff_at(legs: tuple[OptionLeg, ...] | list[OptionLeg], underlying: Decimal) -> Decimal:
    """Return expiry P/L for the strategy at an underlying price."""
    if underlying < 0:
        raise ValueError("underlying price cannot be negative")
    total = _ZERO
    for leg in legs:
        lot_size = Decimal(getattr(leg.contract, "lot_size", 1))
        total += _intrinsic(leg, underlying)
        total -= Decimal(leg.quantity) * leg.premium * lot_size
    return total


def _slope(legs: tuple[OptionLeg, ...] | list[OptionLeg], probe: Decimal) -> Decimal:
    """Piecewise-linear slope d(P/L)/d(underlying) in a region."""
    slope = _ZERO
    for leg in legs:
        active = (
            leg.contract.option_type is OptionType.CALL and probe > leg.contract.strike
        ) or (
            leg.contract.option_type is OptionType.PUT and probe < leg.contract.strike
        )
        if active:
            slope += Decimal(leg.quantity) * Decimal(getattr(leg.contract, "lot_size", 1))
    return slope


def _finite_extreme(
    legs: tuple[OptionLeg, ...] | list[OptionLeg], strikes: list[Decimal], maximum: bool
) -> Decimal | None:
    """Find an expiry P/L extreme, returning None for an unbounded side."""
    candidates = [payoff_at(legs, strike) for strike in strikes]
    if not strikes:
        return None

    ordered = sorted(set(strikes))
    left_probe = ordered[0] / Decimal("2") if ordered[0] > 0 else _ZERO
    right_probe = ordered[-1] + max(Decimal("1"), ordered[-1] * Decimal("0.01"))
    left_slope = _slope(legs, left_probe)
    right_slope = _slope(legs, right_probe)

    if maximum:
        if left_slope > 0 or right_slope > 0:
            return None
        return max(candidates)
    if left_slope < 0 or right_slope < 0:
        return None
    return min(candidates)


def _breakevens(legs: tuple[OptionLeg, ...] | list[OptionLeg]) -> tuple[Decimal, ...]:
    strikes = sorted(set(leg.contract.strike for leg in legs))
    if not strikes:
        return ()
    points = [Decimal("0"), *strikes]
    roots: set[Decimal] = set()

    # Every expiry payoff segment is linear. Include the finite segments plus
    # the origin; roots outside the strike envelope are handled by the tails.
    boundaries = sorted(set(points))
    probes: list[Decimal] = []
    for index, boundary in enumerate(boundaries):
        probes.append(boundary)
        if index + 1 < len(boundaries):
            probes.append((boundary + boundaries[index + 1]) / Decimal("2"))
    right_probe = boundaries[-1] + max(Decimal("1"), boundaries[-1] * Decimal("0.01"))
    probes.append(right_probe)

    for index, probe in enumerate(probes):
        value = payoff_at(legs, probe)
        if value == 0:
            roots.add(probe)
            continue
        if index + 1 >= len(probes):
            continue
        next_probe = probes[index + 1]
        next_value = payoff_at(legs, next_probe)
        if value * next_value < 0:
            slope = _slope(legs, (probe + next_probe) / Decimal("2"))
            if slope != 0:
                root = probe - value / slope
                if root >= 0:
                    roots.add(root)

    # Check each open interval directly using its linear slope.
    for low, high in zip(boundaries, boundaries[1:]):
        slope = _slope(legs, (low + high) / Decimal("2"))
        low_value = payoff_at(legs, low)
        if slope != 0:
            root = low - low_value / slope
            if low <= root <= high:
                roots.add(root)

    return tuple(sorted(roots))


def payoff_report(legs: tuple[OptionLeg, ...] | list[OptionLeg]) -> OptionPayoffReport:
    if not legs:
        raise ValueError("at least one option leg is required")

    strikes = [leg.contract.strike for leg in legs]
    maximum_profit = _finite_extreme(legs, strikes, maximum=True)
    maximum_loss = _finite_extreme(legs, strikes, maximum=False)
    capital_requirement = abs(maximum_loss) if maximum_loss is not None and maximum_loss < 0 else _ZERO
    risk_reward = None
    if maximum_profit is not None and maximum_loss is not None and maximum_loss < 0:
        risk_reward = maximum_profit / abs(maximum_loss) if maximum_profit >= 0 else None

    return OptionPayoffReport(
        maximum_profit=maximum_profit,
        maximum_loss=maximum_loss,
        breakeven=_breakevens(legs),
        capital_requirement=capital_requirement,
        risk_reward=risk_reward,
    )
