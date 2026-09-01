from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Protocol, Sequence

from app.market.models import Candle


class Side(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass(frozen=True)
class MarketOrder:
    side: Side
    quantity: Decimal
    entry_price: Decimal
    stop_price: Decimal | None = None
    target_price: Decimal | None = None


class BacktestStrategy(Protocol):
    def on_candle(self, candles: Sequence[Candle]) -> MarketOrder | None: ...


@dataclass(frozen=True)
class BacktestOrderEvent:
    sequence: int
    event: str
    side: Side
    quantity: Decimal
    price: Decimal
    timestamp: object


@dataclass(frozen=True)
class BacktestTrade:
    side: Side
    quantity: Decimal
    entry_price: Decimal
    exit_price: Decimal
    gross_pnl: Decimal
    fees: Decimal
    slippage: Decimal
    net_pnl: Decimal


@dataclass
class BacktestResult:
    starting_balance: Decimal
    ending_balance: Decimal
    trades: list[BacktestTrade] = field(default_factory=list)
    equity_curve: list[Decimal] = field(default_factory=list)
    order_events: list[BacktestOrderEvent] = field(default_factory=list)

    @property
    def net_pnl(self) -> Decimal:
        return self.ending_balance - self.starting_balance

    @property
    def win_rate(self) -> Decimal:
        if not self.trades:
            return Decimal("0")
        return Decimal(sum(t.net_pnl > 0 for t in self.trades)) / Decimal(len(self.trades)) * Decimal("100")

    @property
    def max_drawdown(self) -> Decimal:
        peak = self.starting_balance
        max_dd = Decimal("0")
        for equity in self.equity_curve:
            peak = max(peak, equity)
            max_dd = max(max_dd, peak - equity)
        return max_dd

    @property
    def expectancy(self) -> Decimal:
        if not self.trades:
            return Decimal("0")
        return sum((t.net_pnl for t in self.trades), Decimal("0")) / Decimal(len(self.trades))


@dataclass
class _OpenPosition:
    order: MarketOrder
    entry_fill: Decimal
    entry_timestamp: object


class BacktestEngine:
    """Deterministic candle-by-candle simulator with no future-data access."""

    def __init__(self, candles: Sequence[Candle], starting_balance: Decimal = Decimal("100000"),
                 fee_rate: Decimal = Decimal("0"), slippage_bps: Decimal = Decimal("0")):
        if starting_balance < 0 or fee_rate < 0 or slippage_bps < 0:
            raise ValueError("starting_balance, fee_rate and slippage_bps must be non-negative")
        ordered = sorted(enumerate(candles), key=lambda x: (x[1].timestamp, x[0]))
        self._candles = tuple(c for _, c in ordered)
        self.starting_balance = starting_balance
        self.fee_rate = fee_rate
        self.slippage_bps = slippage_bps

    @property
    def candles(self) -> tuple[Candle, ...]:
        return self._candles

    def out_of_sample_split(self, train_ratio: Decimal) -> tuple["BacktestEngine", "BacktestEngine"]:
        """Split chronologically; the test set is strictly later than training data."""
        if train_ratio <= 0 or train_ratio >= 1:
            raise ValueError("train_ratio must be between 0 and 1")
        cut = int(len(self._candles) * train_ratio)
        if cut == 0 or cut == len(self._candles):
            raise ValueError("train_ratio produces an empty split")
        kwargs = dict(starting_balance=self.starting_balance, fee_rate=self.fee_rate, slippage_bps=self.slippage_bps)
        return BacktestEngine(self._candles[:cut], **kwargs), BacktestEngine(self._candles[cut:], **kwargs)

    def run(self, strategy: BacktestStrategy) -> BacktestResult:
        balance = self.starting_balance
        visible: list[Candle] = []
        trades: list[BacktestTrade] = []
        events: list[BacktestOrderEvent] = []
        equity = [balance]
        position: _OpenPosition | None = None

        for sequence, candle in enumerate(self._candles):
            visible.append(candle)

            if position is not None:
                exit_price = self._resolve_exit(position.order, candle)
                if exit_price is not None:
                    trade, balance = self._close_position(position, exit_price, candle.timestamp, balance)
                    trades.append(trade)
                    events.append(BacktestOrderEvent(sequence, "CLOSE", position.order.side,
                                                     position.order.quantity, trade.exit_price, candle.timestamp))
                    position = None

            if position is None:
                order = strategy.on_candle(tuple(visible))
                if order is not None:
                    self._validate_order(order, candle)
                    entry = self._fill_price(order.entry_price, order.side, entering=True)
                    position = _OpenPosition(order, entry, candle.timestamp)
                    events.append(BacktestOrderEvent(sequence, "OPEN", order.side, order.quantity, entry, candle.timestamp))
                    exit_price = self._resolve_exit(order, candle)
                    if exit_price is not None:
                        trade, balance = self._close_position(position, exit_price, candle.timestamp, balance)
                        trades.append(trade)
                        events.append(BacktestOrderEvent(sequence, "CLOSE", order.side, order.quantity,
                                                         trade.exit_price, candle.timestamp))
                        position = None

            equity.append(balance)

        if position is not None and self._candles:
            last = self._candles[-1]
            trade, balance = self._close_position(position, last.close, last.timestamp, balance)
            trades.append(trade)
            events.append(BacktestOrderEvent(len(self._candles), "CLOSE_END", position.order.side,
                                             position.order.quantity, trade.exit_price, last.timestamp))
            equity[-1] = balance

        return BacktestResult(self.starting_balance, balance, trades, equity, events)

    def _validate_order(self, order: MarketOrder, candle: Candle) -> None:
        if order.quantity <= 0 or order.entry_price <= 0:
            raise ValueError("order quantity and entry price must be positive")
        if order.stop_price is not None and order.stop_price <= 0:
            raise ValueError("stop price must be positive")
        if order.target_price is not None and order.target_price <= 0:
            raise ValueError("target price must be positive")
        if order.entry_price < candle.low or order.entry_price > candle.high:
            raise ValueError("backtest order cannot fill outside the current candle")

    def _resolve_exit(self, order: MarketOrder, candle: Candle) -> Decimal | None:
        if order.stop_price is not None and ((order.side == Side.LONG and candle.low <= order.stop_price) or
                                             (order.side == Side.SHORT and candle.high >= order.stop_price)):
            return order.stop_price
        if order.target_price is not None and ((order.side == Side.LONG and candle.high >= order.target_price) or
                                               (order.side == Side.SHORT and candle.low <= order.target_price)):
            return order.target_price
        return None

    def _close_position(self, position: _OpenPosition, exit_price: Decimal, timestamp: object,
                        balance: Decimal) -> tuple[BacktestTrade, Decimal]:
        order = position.order
        exit_fill = self._fill_price(exit_price, order.side, entering=False)
        gross = (exit_fill - position.entry_fill) * order.quantity
        if order.side == Side.SHORT:
            gross = -gross
        notional = abs(position.entry_fill * order.quantity) + abs(exit_fill * order.quantity)
        fees = notional * self.fee_rate
        slippage = abs(position.entry_fill - order.entry_price) * order.quantity + abs(exit_fill - exit_price) * order.quantity
        net = gross - fees
        return BacktestTrade(order.side, order.quantity, position.entry_fill, exit_fill, gross, fees, slippage, net), balance + net

    def _fill_price(self, price: Decimal, side: Side, entering: bool) -> Decimal:
        bps = self.slippage_bps / Decimal("10000")
        adverse = (side == Side.LONG) == entering
        return price * (Decimal("1") + bps if adverse else Decimal("1") - bps)
