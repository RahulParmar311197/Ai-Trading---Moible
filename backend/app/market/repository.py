"""Repository boundary for instrument persistence.

The concrete database implementation can be introduced without leaking storage
concerns into market-domain services.
"""

from abc import ABC, abstractmethod

from .models import Instrument


class InstrumentRepository(ABC):
    @abstractmethod
    def get(self, instrument_id: str) -> Instrument | None:
        raise NotImplementedError

    @abstractmethod
    def upsert(self, instrument: Instrument) -> Instrument:
        raise NotImplementedError

    @abstractmethod
    def list_active(self) -> list[Instrument]:
        raise NotImplementedError


class InMemoryInstrumentRepository(InstrumentRepository):
    """Deterministic repository used by unit tests and local development."""

    def __init__(self) -> None:
        self._items: dict[str, Instrument] = {}

    def get(self, instrument_id: str) -> Instrument | None:
        return self._items.get(instrument_id)

    def upsert(self, instrument: Instrument) -> Instrument:
        self._items[instrument.id] = instrument
        return instrument

    def list_active(self) -> list[Instrument]:
        return [item for item in self._items.values() if item.active]
