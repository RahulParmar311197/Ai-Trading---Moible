"""Application service for instrument lifecycle operations."""

from .models import Instrument
from .repository import InstrumentRepository


class InstrumentService:
    def __init__(self, repository: InstrumentRepository) -> None:
        self.repository = repository

    def get(self, instrument_id: str) -> Instrument | None:
        return self.repository.get(instrument_id)

    def upsert(self, instrument: Instrument) -> Instrument:
        return self.repository.upsert(instrument)

    def active_instruments(self) -> list[Instrument]:
        return self.repository.list_active()
