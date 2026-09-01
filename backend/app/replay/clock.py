from enum import Enum


class ReplaySpeed(str, Enum):
    X0_5 = "0.5x"
    X1 = "1x"
    X2 = "2x"
    X5 = "5x"
    X10 = "10x"


class ReplayClock:
    """Small deterministic clock over an already ordered event sequence."""

    def __init__(self, event_count: int, speed: ReplaySpeed = ReplaySpeed.X1):
        if event_count < 0:
            raise ValueError("event_count must be non-negative")
        self._count = event_count
        self._index = -1
        self._paused = True
        self._speed = speed

    @property
    def index(self) -> int:
        return self._index

    @property
    def paused(self) -> bool:
        return self._paused

    @property
    def speed(self) -> ReplaySpeed:
        return self._speed

    @property
    def finished(self) -> bool:
        return self._count == 0 or self._index >= self._count - 1

    def play(self) -> None:
        self._paused = False

    def pause(self) -> None:
        self._paused = True

    def reset(self) -> None:
        self._index = -1
        self._paused = True

    def set_speed(self, speed: ReplaySpeed) -> None:
        self._speed = speed

    def next(self) -> int | None:
        if self.finished:
            return None
        self._index += 1
        return self._index

    def previous(self) -> int | None:
        if self._index < 0:
            return None
        self._index -= 1
        return self._index
