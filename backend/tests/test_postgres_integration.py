"""Live PostgreSQL integration test for the instrument repository.

The test is opt-in through TEST_DATABASE_URL so normal unit-test runs never
require an external database.
"""

import os
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from app.database.session import SQLAlchemyExecutor, create_database_engine
from app.market.models import Instrument, InstrumentType
from app.market.postgres_repository import PostgresInstrumentRepository


@pytest.mark.integration
def test_instrument_repository_against_postgres() -> None:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not configured")

    root = Path(__file__).resolve().parents[2]
    engine = create_database_engine(database_url)
    with engine.begin() as connection:
        connection.exec_driver_sql((root / "database/migrations/001_initial.sql").read_text())
        connection.exec_driver_sql((root / "database/migrations/002_instruments.sql").read_text())

    repository = PostgresInstrumentRepository(SQLAlchemyExecutor(engine))
    instrument = Instrument(
        id="integration-nifty-front",
        symbol="NIFTY",
        exchange="NSE",
        market="equity_derivatives",
        instrument_type=InstrumentType.FUTURE,
        expiry=datetime(2026, 9, 24, tzinfo=timezone.utc),
        strike=Decimal("25000"),
        lot_size=75,
        tick_size=Decimal("0.05"),
    )

    repository.upsert(instrument)
    assert repository.get(instrument.id) == instrument
    assert instrument in repository.list_active()

    with engine.begin() as connection:
        connection.exec_driver_sql(
            "DELETE FROM instruments WHERE id = 'integration-nifty-front'"
        )
    engine.dispose()
