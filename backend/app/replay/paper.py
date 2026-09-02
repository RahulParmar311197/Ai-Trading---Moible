from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence

from app.backtest.engine import BacktestStrategy, MarketOrder, Side
from app.market.models import Candle
from app.paper.models import Order, OrderSide, OrderType
from app.paper.engine import PaperBroker

from .engine import ReplayEngine
from .state import ReplayMarketState


@dataclass(frozen=True)
class ReplayPaperExecution:
    """A deterministic replay signal and the paper order it produced."""

    sequence: int
    timestamp: object
    order_id: str
    source: MarketOrder


class ReplayPaperSession:
    """Connect replay-visible candles to the paper broker only.

    This boundary deliberately accepts a ``PaperBroker`` rather than a generic
    broker. Replay therefore cannot route orders to Upstox, Dhan, or any other
    live provider. Strategy evaluation sees only candles visible at the current
    replay index.
    """

    def __init__(self, replay: ReplayEngine, paper: PaperBroker, strategy: BacktestStrategy) -> None:
        self.replay = replay
        self.paper = paper
        self.strategy = strategy
        self.executions: list[ReplayPaperExecution] = []
        self._brackets: dict[str, MarketOrder] = {}

    def reset(self) -> ReplayMarketState:
        self.executions.clear()
        self._brackets.clear()
        return self.replay.reset()

    def step(self) -> ReplayMarketState | None:
        state = self.replay.step()
        if state is None:
            return None
        self._process_open_brackets(state)
        signal = self.strategy.on_candle(state.candles)
        if signal is not None:
            self._submit_signal(state, signal)
        return state

    def run(self) -> ReplayMarketState:
        self.reset()
        self.replay.clock.play()
        while not self.replay.clock.finished:
            self.step()
        self.replay.clock.pause()
        return self.replay.state

    def _submit_signal(self, state: ReplayMarketState, signal: MarketOrder) -> None:
        quantity = self._integer_quantity(signal.quantity)
        candle = state.candles[-1]
        if signal.entry_price <= 0 or signal.entry_price < candle.low or signal.entry_price > candle.high:
            raise ValueError("replay paper entry must be inside the current candle")

        order_id = f"replay-{state.current_index:08d}"
        if signal.side is Side.LONG:
            side = OrderSide.BUY
        elif signal.side is Side.SHORT:
            side = OrderSide.SELL
        else:
            raise ValueError(f"unsupported replay side: {signal.side}")

        order = Order(
            order_id=order_id,
            symbol=candle.instrument_id,
            side=side,
            order_type=OrderType.MARKET,
            quantity=quantity,
            created_at=candle.timestamp,
        )
        self.paper.place_order(order, signal.entry_price)
        self.executions.append(ReplayPaperExecution(state.current_index, state.current_timestamp, order_id, signal))
        if signal.stop_price is not None or signal.target_price is not None:
            self._brackets[order_id] = signal

    def _process_open_brackets(self, state: ReplayMarketState) -> None:
        if not self._brackets:
            return
        candle = state.candles[-1]
        for entry_id, signal in tuple(self._brackets.items()):
            if signal.side is Side.LONG:
                if signal.stop_price is not None and candle.low <= signal.stop_price:
                    self._close(entry_id, signal, signal.stop_price, state)
                elif signal.target_price is not None and candle.high >= signal.target_price:
                    self._close(entry_id, signal, signal.target_price, state)
            else:
                if signal.stop_price is not None and candle.high >= signal.stop_price:
                    self._close(entry_id, signal, signal.stop_price, state)
                elif signal.target_price is not None and candle.low <= signal.target_price:
                    self._close(entry_id, signal, signal.target_price, state)

    def _close(self, entry_id: str, signal: MarketOrder, price: Decimal, state: ReplayMarketState) -> None:
        entry = self.paper.orders[entry_id]
        quantity = entry.filled_quantity
        if quantity <= 0:
            self._brackets.pop(entry_id, None)
            return
        candle = state.candles[-1]
        exit_id = f"{entry_id}-exit-{state.current_index:08d}"
        side = OrderSide.SELL if signal.side is Side.LONG else OrderSide.BUY
        order = Order(
            order_id=exit_id,
            symbol=candle.instrument_id,
            side=side,
            order_type=OrderType.MARKET,
            quantity=quantity,
            created_at=candle.timestamp,
        )
        self.paper.place_order(order, price)
        self._brackets.pop(entry_id, None)

    @staticmethod
    def _integer_quantity(quantity: Decimal | None) -> int:
        if quantity is None:
            raise ValueError("replay paper execution requires an explicit quantity")
        if quantity <= 0 or quantity != quantity.to_integral_value():
            raise ValueError("replay paper quantity must be a positive whole number")
        return int(quantity)
