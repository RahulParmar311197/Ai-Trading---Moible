"""SQL representation helpers for canonical instrument persistence."""

from .models import Instrument


def instrument_to_params(instrument: Instrument) -> dict[str, object]:
    """Map the domain model to the columns defined by migration 002."""
    return instrument.model_dump()
