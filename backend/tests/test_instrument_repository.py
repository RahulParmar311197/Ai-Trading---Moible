from app.market.models import Instrument, InstrumentType
from app.market.repository import InMemoryInstrumentRepository
from app.market.service import InstrumentService


def make_instrument(instrument_id: str, active: bool = True) -> Instrument:
    return Instrument(
        id=instrument_id,
        symbol="NIFTY",
        exchange="NSE",
        market="equity_derivatives",
        instrument_type=InstrumentType.FUTURE,
        active=active,
    )


def test_repository_upsert_and_get() -> None:
    repository = InMemoryInstrumentRepository()
    instrument = make_instrument("nifty-front")
    repository.upsert(instrument)
    assert repository.get("nifty-front") == instrument


def test_service_lists_only_active_instruments() -> None:
    repository = InMemoryInstrumentRepository()
    service = InstrumentService(repository)
    service.upsert(make_instrument("active"))
    service.upsert(make_instrument("inactive", active=False))
    assert [item.id for item in service.active_instruments()] == ["active"]
