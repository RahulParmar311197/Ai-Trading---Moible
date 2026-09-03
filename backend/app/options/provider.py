from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime, timezone
from decimal import Decimal

import httpx

from .models import OptionChain, OptionContract, OptionType


class OptionChainProvider(ABC):
    """Provider-neutral boundary for live option-chain data."""

    @abstractmethod
    async def get_option_chain(self, underlying: str, expiry: date | None = None) -> OptionChain:
        raise NotImplementedError


class OptionChainProviderError(RuntimeError):
    """Raised when a live option-chain provider cannot return valid data."""


class UnconfiguredOptionChainProvider(OptionChainProvider):
    """Safe default: live options remain unavailable until a provider is configured."""

    async def get_option_chain(self, underlying: str, expiry: date | None = None) -> OptionChain:
        raise OptionChainProviderError("live option-chain provider is not configured")


class UpstoxOptionChainProvider(OptionChainProvider):
    """Upstox v2 option-chain adapter mapped into the provider-neutral contract.

    ``underlying`` is the Upstox instrument key (for example
    ``NSE_INDEX|Nifty 50``). An explicit expiry is required because both the
    Upstox put/call and option-contract endpoints require it for a precise
    chain. Contract metadata is fetched alongside quotes so lot size and the
    broker trading symbol are never silently defaulted.
    """

    _CHAIN_URL = "https://api.upstox.com/v2/option/chain"
    _CONTRACT_URL = "https://api.upstox.com/v2/option/contract"

    def __init__(self, access_token: str, *, timeout: float = 10.0, client: httpx.AsyncClient | None = None) -> None:
        if not access_token.strip():
            raise ValueError("Upstox option-chain access token is required")
        if timeout <= 0:
            raise ValueError("option-chain timeout must be positive")
        self.access_token = access_token
        self.timeout = timeout
        self._client = client

    async def get_option_chain(self, underlying: str, expiry: date | None = None) -> OptionChain:
        if not underlying.strip():
            raise ValueError("option-chain underlying is required")
        if expiry is None:
            raise ValueError("option-chain expiry is required")

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }
        params = {"instrument_key": underlying, "expiry_date": expiry.isoformat()}
        own_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self.timeout)
        try:
            chain_response = await client.get(self._CHAIN_URL, params=params, headers=headers)
            chain_response.raise_for_status()
            chain_payload = chain_response.json()

            contract_response = await client.get(self._CONTRACT_URL, params=params, headers=headers)
            contract_response.raise_for_status()
            contract_payload = contract_response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OptionChainProviderError("Upstox option-chain request failed") from exc
        finally:
            if own_client:
                await client.aclose()

        try:
            if chain_payload.get("status") != "success" or not isinstance(chain_payload.get("data"), list):
                raise OptionChainProviderError("Upstox returned an invalid option-chain response")
            if contract_payload.get("status") != "success" or not isinstance(contract_payload.get("data"), list):
                raise OptionChainProviderError("Upstox returned invalid option-contract metadata")

            metadata_by_key: dict[str, dict] = {}
            for metadata in contract_payload["data"]:
                if not isinstance(metadata, dict) or not metadata.get("instrument_key"):
                    raise OptionChainProviderError("Upstox returned malformed option-contract metadata")
                key = str(metadata["instrument_key"])
                if key in metadata_by_key:
                    raise OptionChainProviderError("Upstox returned duplicate option-contract metadata")
                metadata_by_key[key] = metadata

            contracts: list[OptionContract] = []
            for row in chain_payload["data"]:
                row_expiry = date.fromisoformat(str(row["expiry"]))
                if row_expiry != expiry:
                    raise OptionChainProviderError("Upstox returned an unexpected option expiry")
                strike = Decimal(str(row["strike_price"]))
                underlying_key = str(row["underlying_key"])
                for key, option_type, expected_type in (
                    ("call_options", OptionType.CALL, "CE"),
                    ("put_options", OptionType.PUT, "PE"),
                ):
                    option = row.get(key)
                    if not isinstance(option, dict):
                        continue
                    market = option.get("market_data")
                    greeks = option.get("option_greeks") or {}
                    if not isinstance(market, dict):
                        raise OptionChainProviderError("Upstox option market data is missing")
                    required_market = ("bid_price", "ask_price", "ltp", "volume", "oi")
                    if any(field not in market or market[field] is None for field in required_market):
                        raise OptionChainProviderError("Upstox option market data is incomplete")
                    instrument_key = str(option.get("instrument_key", ""))
                    if not instrument_key:
                        raise OptionChainProviderError("Upstox option instrument key is missing")
                    metadata = metadata_by_key.get(instrument_key)
                    if metadata is None:
                        raise OptionChainProviderError(
                            "Upstox option-contract metadata is missing for a chain instrument"
                        )
                    if str(metadata.get("instrument_type")) != expected_type:
                        raise OptionChainProviderError("Upstox option-contract type does not match chain side")
                    if date.fromisoformat(str(metadata["expiry"])) != expiry:
                        raise OptionChainProviderError("Upstox option-contract metadata has an unexpected expiry")
                    lot_size = int(metadata["lot_size"])
                    if lot_size <= 0:
                        raise OptionChainProviderError("Upstox returned an invalid option lot size")
                    if str(metadata["underlying_key"]) != underlying_key:
                        raise OptionChainProviderError("Upstox option-contract underlying does not match chain")
                    if Decimal(str(metadata["strike_price"])) != strike:
                        raise OptionChainProviderError("Upstox option-contract strike does not match chain")
                    contracts.append(
                        OptionContract(
                            symbol=str(metadata["trading_symbol"]),
                            underlying=underlying_key,
                            expiry=row_expiry,
                            strike=strike,
                            option_type=option_type,
                            lot_size=lot_size,
                            bid=Decimal(str(market["bid_price"])),
                            ask=Decimal(str(market["ask_price"])),
                            ltp=Decimal(str(market["ltp"])),
                            volume=int(market["volume"]),
                            open_interest=int(market["oi"]),
                            # Upstox reports IV as a percentage; the internal
                            # contract stores IV as a decimal fraction.
                            iv=Decimal(str(greeks["iv"])) / Decimal("100") if greeks.get("iv") is not None else None,
                            delta=Decimal(str(greeks["delta"])) if greeks.get("delta") is not None else None,
                            gamma=Decimal(str(greeks["gamma"])) if greeks.get("gamma") is not None else None,
                            theta=Decimal(str(greeks["theta"])) if greeks.get("theta") is not None else None,
                            vega=Decimal(str(greeks["vega"])) if greeks.get("vega") is not None else None,
                        )
                    )
            if not contracts:
                raise OptionChainProviderError("Upstox returned an empty option chain")
            return OptionChain(
                underlying=underlying,
                as_of=datetime.now(timezone.utc),
                contracts=tuple(contracts),
            )
        except OptionChainProviderError:
            raise
        except (KeyError, TypeError, ValueError, ArithmeticError) as exc:
            raise OptionChainProviderError("Upstox returned malformed option-chain data") from exc
