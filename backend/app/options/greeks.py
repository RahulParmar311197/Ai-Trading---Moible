"""Deterministic Black-Scholes pricing and first-order Greeks.

Inputs use decimal prices/rates and annualized volatility/time. Theta is
reported per year and vega per one whole unit of volatility (100 percentage
points), matching the mathematical derivatives; callers may scale for UI.
"""

from dataclasses import dataclass
from decimal import Decimal
from math import erf, exp, log, pi, sqrt

from .models import OptionType


@dataclass(frozen=True)
class Greeks:
    price: Decimal
    delta: Decimal
    gamma: Decimal
    theta: Decimal
    vega: Decimal
    rho: Decimal


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))


def _norm_pdf(x: float) -> float:
    return exp(-0.5 * x * x) / sqrt(2.0 * pi)


def black_scholes(
    spot: Decimal,
    strike: Decimal,
    time_years: Decimal,
    volatility: Decimal,
    rate: Decimal = Decimal("0"),
    dividend_yield: Decimal = Decimal("0"),
    option_type: OptionType = OptionType.CALL,
) -> Greeks:
    if spot <= 0 or strike <= 0:
        raise ValueError("spot and strike must be positive")
    if time_years < 0:
        raise ValueError("time to expiry cannot be negative")
    if volatility < 0:
        raise ValueError("volatility cannot be negative")
    if time_years == 0 or volatility == 0:
        intrinsic = max(spot - strike, Decimal("0")) if option_type is OptionType.CALL else max(strike - spot, Decimal("0"))
        delta = Decimal("1") if spot > strike and option_type is OptionType.CALL else Decimal("-1") if spot < strike and option_type is OptionType.PUT else Decimal("0")
        return Greeks(intrinsic, delta, Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"))

    s, k, t, sigma, r, q = map(float, (spot, strike, time_years, volatility, rate, dividend_yield))
    root_t = sqrt(t)
    d1 = (log(s / k) + (r - q + 0.5 * sigma * sigma) * t) / (sigma * root_t)
    d2 = d1 - sigma * root_t
    nd1 = _norm_cdf(d1)
    nd2 = _norm_cdf(d2)
    pdf = _norm_pdf(d1)
    disc_r = exp(-r * t)
    disc_q = exp(-q * t)

    if option_type is OptionType.CALL:
        price = s * disc_q * nd1 - k * disc_r * nd2
        delta = disc_q * nd1
        theta = -(s * disc_q * pdf * sigma) / (2 * root_t) - r * k * disc_r * nd2 + q * s * disc_q * nd1
        rho = k * t * disc_r * nd2
    else:
        price = k * disc_r * _norm_cdf(-d2) - s * disc_q * _norm_cdf(-d1)
        delta = -disc_q * _norm_cdf(-d1)
        theta = -(s * disc_q * pdf * sigma) / (2 * root_t) + r * k * disc_r * _norm_cdf(-d2) - q * s * disc_q * _norm_cdf(-d1)
        rho = -k * t * disc_r * _norm_cdf(-d2)

    gamma = disc_q * pdf / (s * sigma * root_t)
    vega = s * disc_q * pdf * root_t
    return Greeks(Decimal(str(price)), Decimal(str(delta)), Decimal(str(gamma)), Decimal(str(theta)), Decimal(str(vega)), Decimal(str(rho)))
