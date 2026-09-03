from pathlib import Path

import pytest

from app.brokers.catalogue import InstrumentCatalogueError, load_dhan_catalogue_csv
from app.brokers.order_config import ExchangeSegment, OptionType


_OPTION_HEADER = (
    "SEM_EXM_EXCH_ID,SEM_SEGMENT,SEM_SMST_SECURITY_ID,SEM_TRADING_SYMBOL,"
    "SEM_LOT_UNITS,SEM_EXPIRY_DATE,SEM_STRIKE_PRICE,SEM_OPTION_TYPE\n"
)


def test_load_dhan_catalogue_csv_preserves_authoritative_option_metadata(tmp_path: Path) -> None:
    path = tmp_path / "dhan.csv"
    path.write_text(
        _OPTION_HEADER
        + "NSE,D,42528,NIFTY25SEP25000CE,75,2025-09-25,25000,CE\n",
        encoding="utf-8",
    )

    instruments = load_dhan_catalogue_csv(str(path))

    item = instruments[0]
    assert item.provider_symbol == "42528"
    assert item.exchange_segment is ExchangeSegment.NSE_FNO
    assert item.lot_size == 75
    assert item.option_metadata is not None
    assert item.option_metadata.option_type is OptionType.CALL
    assert str(item.option_metadata.strike) == "25000"


def test_load_dhan_catalogue_csv_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(InstrumentCatalogueError, match="file is not available"):
        load_dhan_catalogue_csv(str(tmp_path / "missing.csv"))


def test_load_dhan_catalogue_csv_rejects_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")

    with pytest.raises(InstrumentCatalogueError, match="header is missing"):
        load_dhan_catalogue_csv(str(path))
