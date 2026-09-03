from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

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
    ``NSE_INDEX|Nifty 50``). An explicit expiry is required because the Upstox
    put/call endpoint requires one; the adapter never guesses an expiry.
    """

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
            response = await client.get("https://api.upstox.com/v2/option/chain", params=params, headers=headers)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OptionChainProviderError("Upstox option-chain request failed") from exc
        finally:
            if own_client:
                await client.aclose()

        try:
            if payload.get("status") != "success" or not isinstance(payload.get("data"), list):
                raise OptionChainProviderError("Upstox returned an invalid option-chain response")
            contracts: list[OptionContract] = []
            for row in payload["data"]:
                row_expiry = date.fromisoformat(str(row["expiry"]))
                strike = Decimal(str(row["strike_price"]))
                underlying_key = str(row["underlying_key"])
                for key, option_type in (("call_options", OptionType.CALL), ("put_options", OptionType.PUT)):
                    option = row.get(key)
                    if not isinstance(option, dict):
                        continue
                    market = option.get("market_data") or {}
                    greeks = option.get("option_greeks") or {}
                    instrument_key = str(option["instrument_key"])
                    contracts.append(
                        OptionContract(
                            symbol=instrument_key,
                            underlying=underlying_key,
                            expiry=row_expiry,
                            strike=strike,
                            option_type=option_type,
                            bid=Decimal(str(market.get("bid_price", 0))),
                            ask=Decimal(str(market.get("ask_price", 0))),
                            ltp=Decimal(str(market.get("ltp", 0))),
                            volume=int(market.get("volume", 0)),
                            open_interest=int(market.get("oi", 0)),
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
        except (KeyError, TypeError, ValueError, ArithmeticError) as exc:
            if isinstance(exc, OptionChainProviderError):
                raise
            raise OptionChainProviderError("Upstox returned malformed option-chain data") from exc
