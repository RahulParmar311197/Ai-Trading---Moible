from decimal import Decimal

from .models import OptionChain, OptionContract, OptionLiquidityLimits, OptionSelection


def spread_percent(contract: OptionContract) -> Decimal | None:
    if contract.bid <= 0 or contract.ask <= 0:
        return None
    mid = (contract.bid + contract.ask) / Decimal("2")
    if mid <= 0:
        return None
    return (contract.ask - contract.bid) / mid


def liquid(contract: OptionContract, limits: OptionLiquidityLimits) -> bool:
    spread = spread_percent(contract)
    return (
        contract.volume >= limits.min_volume
        and contract.open_interest >= limits.min_open_interest
        and spread is not None
        and spread <= limits.max_spread_percent
        and contract.ltp > 0
    )


def select_by_delta(chain: OptionChain, target_delta: Decimal, limits: OptionLiquidityLimits) -> OptionSelection | None:
    eligible = [c for c in chain.contracts if liquid(c, limits) and c.delta is not None]
    if not eligible:
        return None
    chosen = min(eligible, key=lambda c: (abs(c.delta - target_delta), c.strike, c.symbol))
    return OptionSelection(contract=chosen, score=Decimal("1") - abs(chosen.delta - target_delta))
