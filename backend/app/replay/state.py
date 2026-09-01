from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from app.market.models import Candle


@dataclass(frozen=True)
class ReplayMarketState:
    """The market view available at the current replay timestamp only."""

    current_index: int
    current_timestamp: datetime | None
    candles: tuple[Candle, ...] = ()

    @property
    def current_candle(self) -> Candle | None:
        return self.candles[-1] if self.candles else None


@dataclass
class ReplayStatistics:
    starting_balance: Decimal = Decimal("0")
    ending_balance: Decimal = Decimal("0")
    net_pnl: Decimal = Decimal("0")
    trades: int = 0
    wins: int = 0
    losses: int = 0
    r_values: list[Decimal] = field(default_factory=list)

    def record_trade(self, pnl: Decimal, r_multiple: Decimal | None = None) -> None:
        self.trades += 1
        self.net_pnl += pnl
        self.ending_balance += pnl
        if pnl > 0:
            self.wins += 1
        elif pnl < 0:
            self.losses += 1
        if r_multiple is not None:
            self.r_values.append(r_multiple)

    @property
    def win_rate(self) -> Decimal:
        if not self.trades:
            return Decimal("0")
        return (Decimal(self.wins) / Decimal(self.trades)) * Decimal("100")

    @property
    def average_r(self) -> Decimal:
        if not self.r_values:
            return Decimal("0")
        return sum(self.r_values, Decimal("0")) / Decimal(len(self.r_values))
