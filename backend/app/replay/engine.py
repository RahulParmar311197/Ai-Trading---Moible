from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Iterable, Protocol

from app.market.models import Candle, Timeframe
from app.smc.engine import SmcEngine, SmcAnalysis

from .clock import ReplayClock, ReplaySpeed
from .state import ReplayMarketState, ReplayStatistics


class HistoricalCandleSource(Protocol):
    def list_range(self, instrument_id: str, timeframe: str, start_time, end_time) -> list[Candle]: ...


@dataclass(frozen=True)
class ReplayEvent:
    sequence: int
    candle: Candle


class ReplayEngine:
    """Deterministic, look-ahead-safe candle replay engine."""

    def __init__(self, candles: Iterable[Candle], timeframe: Timeframe | None = None,
                 speed: ReplaySpeed = ReplaySpeed.X1, starting_balance=None):
        ordered = list(enumerate(candles))
        if timeframe is not None:
            ordered = [(i, c) for i, c in ordered if c.timeframe == timeframe]
        ordered.sort(key=lambda item: (item[1].timestamp, item[0]))
        self._events = tuple(ReplayEvent(n, candle) for n, (_, candle) in enumerate(ordered))
        self.clock = ReplayClock(len(self._events), speed)
        self.statistics = ReplayStatistics()
        if starting_balance is not None:
            self.statistics.starting_balance = starting_balance
            self.statistics.ending_balance = starting_balance
        self._callback: Callable[[ReplayMarketState], None] | None = None

    @classmethod
    def from_repository(cls, source: HistoricalCandleSource, instrument_id: str,
                        timeframe: Timeframe, start_time: datetime, end_time: datetime,
                        speed: ReplaySpeed = ReplaySpeed.X1, starting_balance=None) -> "ReplayEngine":
        """Load historical candles through the existing market-data repository boundary."""
        candles = source.list_range(instrument_id, timeframe.value, start_time, end_time)
        return cls(candles, timeframe=timeframe, speed=speed, starting_balance=starting_balance)

    @property
    def events(self) -> tuple[ReplayEvent, ...]:
        return self._events

    @property
    def state(self) -> ReplayMarketState:
        i = self.clock.index
        if i < 0:
            return ReplayMarketState(-1, None, ())
        return ReplayMarketState(
            i,
            self._events[i].candle.timestamp,
            tuple(event.candle for event in self._events[: i + 1]),
        )

    def on_event(self, callback: Callable[[ReplayMarketState], None]) -> None:
        self._callback = callback

    def reset(self) -> ReplayMarketState:
        self.clock.reset()
        self.statistics.net_pnl = 0
        self.statistics.trades = 0
        self.statistics.wins = 0
        self.statistics.losses = 0
        self.statistics.r_values.clear()
        self.statistics.ending_balance = self.statistics.starting_balance
        return self.state

    def step(self) -> ReplayMarketState | None:
        index = self.clock.next()
        if index is None:
            return None
        state = self.state
        if self._callback is not None:
            self._callback(state)
        return state

    def step_previous(self) -> ReplayMarketState:
        self.clock.previous()
        return self.state

    def run(self, callback: Callable[[ReplayMarketState], None] | None = None) -> ReplayMarketState:
        if callback is not None:
            self._callback = callback
        self.clock.play()
        while not self.clock.finished:
            self.step()
        self.clock.pause()
        return self.state

    def run_smc(self, smc: SmcEngine | None = None) -> list[SmcAnalysis]:
        """Replay the existing SMC engine without exposing future candles."""
        analyzer = smc or SmcEngine()
        analyses: list[SmcAnalysis] = []
        self.reset()
        while not self.clock.finished:
            state = self.step()
            if state is not None:
                analyses.append(analyzer.analyze(list(state.candles)))
        self.clock.pause()
        return analyses
