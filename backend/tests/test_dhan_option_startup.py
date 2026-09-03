from pathlib import Path

import pytest

from app.main import _build_option_chain_provider
from app.options.dhan_provider import DhanOptionChainProvider
from app.options.provider import OptionChainProviderError


_OPTION_HEADER = (
    "SEM_EXM_EXCH_ID,SEM_SEGMENT,SEM_SMST_SECURITY_ID,SEM_TRADING_SYMBOL,"
    "SEM_LOT_UNITS,SEM_EXPIRY_DATE,SEM_STRIKE_PRICE,SEM_OPTION_TYPE\n"
)


def _configure_dhan(monkeypatch: pytest.MonkeyPatch, catalogue_path: str) -> None:
    from app.main import settings

    monkeypatch.setattr(settings, "options_provider", "dhan")
    monkeypatch.setattr(settings, "dhan_client_id", "test-client")
    monkeypatch.setattr(settings, "dhan_access_token", "test-token")
    monkeypatch.setattr(settings, "dhan_option_underlying_segment", "IDX_I")
    monkeypatch.setattr(settings, "dhan_option_catalogue_path", catalogue_path)
    monkeypatch.setattr(settings, "options_timeout_seconds", 3.0)


def test_build_option_chain_provider_constructs_dhan_from_authoritative_catalogue(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "dhan.csv"
    path.write_text(
        _OPTION_HEADER
        + "NSE,D,42528,NIFTY25SEP25000CE,75,2025-09-25,25000,CE\n",
        encoding="utf-8",
    )
    _configure_dhan(monkeypatch, str(path))

    provider = _build_option_chain_provider()

    assert isinstance(provider, DhanOptionChainProvider)
    assert provider.client_id == "test-client"
    assert provider.underlying_segment == "IDX_I"
    assert provider.catalogue["42528"].option_metadata is not None


def test_build_option_chain_provider_fails_closed_when_catalogue_is_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _configure_dhan(monkeypatch, str(tmp_path / "missing.csv"))

    with pytest.raises(OptionChainProviderError, match="catalogue is not configured or invalid"):
        _build_option_chain_provider()


def test_build_option_chain_provider_fails_closed_without_credentials(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from app.main import settings

    _configure_dhan(monkeypatch, str(tmp_path / "unused.csv"))
    monkeypatch.setattr(settings, "dhan_access_token", "")

    with pytest.raises(OptionChainProviderError, match="credentials are not configured"):
        _build_option_chain_provider()
