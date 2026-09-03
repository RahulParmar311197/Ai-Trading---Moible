from __future__ import annotations

import asyncio
import time
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

import httpx

from app.brokers.order_config import BrokerInstrument

from .models import OptionChain, OptionContract, OptionType
from .provider import OptionChainProvider, OptionChainProviderError


class DhanOptionChainProvider(OptionChainProvider):
    """DhanHQ v2 option-chain adapter with authoritative catalogue resolution.

    Dhan's option-chain response supplies the option security ID but not the
    execution trading symbol or lot size. Those fields therefore must come
    from the caller-supplied authoritative instrument catalogue; no defaults
    are synthesized.

    ``underlying`` is the Dhan underlying security ID and ``underlying_segment``
    is the Dhan option-chain segment (for example ``IDX_I``).
    """

    _URL = "https://api.dhan.co/v2/optionchain"
    _COOLDOWN_SECONDS = 3.0

    def __init__(
        self,
        client_id: str,
        access_token: str,
        *,
        underlying_segment: str,
        catalogue: dict[str, BrokerInstrument],
        timeout: float = 10.0,
        client: httpx.AsyncClient | None = None,
        clock: Any = time.monotonic,
    ) -> None:
        if not client_id.strip() or not access_token.strip():
            raise ValueError("Dhan option-chain credentials are required")
        if not underlying_segment.strip():
            raise ValueError("Dhan option-chain underlying segment is required")
        if timeout <= 0:
            raise ValueError("option-chain timeout must be positive")
        self.client_id = client_id
        self.access_token = access_token
        self.underlying_segment = underlying_segment.strip()
        self.catalogue = dict(catalogue)
        self.timeout = timeout
        self._client = client
        self._clock = clock
        self._cooldowns: dict[tuple[str, str], float] = {}
        self._cooldown_lock = asyncio.Lock()

    async def _reserve_unique_request(self, underlying: str, expiry: date) -> None:
        key = (underlying, expiry.isoformat())
        now = self._clock()
        async with self._cooldown_lock:
            previous = self._cooldowns.get(key)
            if previous is not None and now - previous < self._COOLDOWN_SECONDS:
                raise OptionChainProviderError(
                    "Dhan option-chain unique request is rate limited; retry after 3 seconds"
                )
            self._cooldowns[key] = now

    async def get_option_chain(self, underlying: str, expiry: date | None = None) -> OptionChain:
        underlying = underlying.strip()
        if not underlying:
            raise ValueError("option-chain underlying is required")
        if expiry is None:
            raise ValueError("option-chain expiry is required")
        if not underlying.isdigit():
            raise ValueError("Dhan option-chain underlying must be a numeric security id")

        await self._reserve_unique_request(underlying, expiry)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "access-token": self.access_token,
            "client-id": self.client_id,
        }
        payload = {
            "UnderlyingScrip": int(underlying),
            "UnderlyingSeg": self.underlying_segment,
            "Expiry": expiry.isoformat(),
        }
        own_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self.timeout)
        try:
            response = await client.post(self._URL, json=payload, headers=headers)
            response.raise_for_status()
            response_payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OptionChainProviderError("Dhan option-chain request failed") from exc
        finally:
            if own_client:
                await client.aclose()

        try:
            if not isinstance(response_payload, dict) or response_payload.get("status") != "success":
                raise OptionChainProviderError("Dhan returned an invalid option-chain response")
            data = response_payload.get("data")
            if not isinstance(data, dict) or not isinstance(data.get("oc"), dict):
                raise OptionChainProviderError("Dhan returned malformed option-chain data")

            contracts: list[OptionContract] = []
            seen_security_ids: set[str] = set()
            for strike_key, strike_data in data["oc"].items():
                if not isinstance(strike_data, dict):
                    raise OptionChainProviderError("Dhan returned malformed strike data")
                try:
                    strike = Decimal(str(strike_key))
                except (ArithmeticError, ValueError) as exc:
                    raise OptionChainProviderError("Dhan returned an invalid option strike") from exc
                if strike <= 0:
                    raise OptionChainProviderError("Dhan returned a non-positive option strike")

                for side_key, option_type in (("ce", OptionType.CALL), ("pe", OptionType.PUT)):
                    option = strike_data.get(side_key)
                    if option is None:
                        continue
                    if not isinstance(option, dict):
                        raise OptionChainProviderError("Dhan returned malformed option data")
                    required = (
                        "security_id", "last_price", "oi", "volume",
                        "top_bid_price", "top_ask_price", "implied_volatility",
                    )
                    if any(field not in option or option[field] is None for field in required):
                        raise OptionChainProviderError("Dhan option market data is incomplete")

                    security_id = str(option["security_id"]).strip()
                    if not security_id or security_id in seen_security_ids:
                        raise OptionChainProviderError("Dhan option security id is missing or duplicated")
                    seen_security_ids.add(security_id)
                    instrument = self.catalogue.get(security_id)
                    if instrument is None:
                        raise OptionChainProviderError(
                            "Dhan option catalogue metadata is missing for a chain instrument"
                        )
                    if instrument.exchange_segment.value != "NSE_FNO" and instrument.exchange_segment.value != "BSE_FNO":
                        raise OptionChainProviderError("Dhan option catalogue instrument is not an F&O contract")

                    # The Dhan option-chain endpoint does not echo expiry/option
                    # type in each leg, so these must be proven by the catalogue
                    # symbol mapping. The catalogue provider is expected to be
                    # sourced from Dhan's instrument master, where those fields
                    # are authoritative. We deliberately do not infer them from
                    # the trading symbol string.
                    metadata = getattr(instrument, "option_metadata", None)
                    if metadata is None:
                        raise OptionChainProviderError(
                            "Dhan option catalogue mapping lacks authoritative expiry/strike/type metadata"
                        )
                    if metadata.expiry != expiry or Decimal(str(metadata.strike)) != strike:
                        raise OptionChainProviderError("Dhan option catalogue metadata does not match chain")
                    if metadata.option_type != option_type:
                        raise OptionChainProviderError("Dhan option catalogue option type does not match chain")

                    greeks = option.get("greeks") or {}
                    if not isinstance(greeks, dict):
                        raise OptionChainProviderError("Dhan option Greeks are malformed")
                    contracts.append(
                        OptionContract(
                            symbol=instrument.canonical_symbol,
                            underlying=underlying,
                            expiry=expiry,
                            strike=strike,
                            option_type=option_type,
                            lot_size=instrument.lot_size,
                            bid=Decimal(str(option["top_bid_price"])),
                            ask=Decimal(str(option["top_ask_price"])),
                            ltp=Decimal(str(option["last_price"])),
                            volume=int(option["volume"]),
                            open_interest=int(option["oi"]),
                            iv=Decimal(str(option["implied_volatility"])) / Decimal("100"),
                            delta=Decimal(str(greeks["delta"])) if greeks.get("delta") is not None else None,
                            gamma=Decimal(str(greeks["gamma"])) if greeks.get("gamma") is not None else None,
                            theta=Decimal(str(greeks["theta"])) if greeks.get("theta") is not None else None,
                            vega=Decimal(str(greeks["vega"])) if greeks.get("vega") is not None else None,
                        )
                    )
            if not contracts:
                raise OptionChainProviderError("Dhan returned an empty option chain")
            return OptionChain(
                underlying=underlying,
                as_of=datetime.now(timezone.utc),
                contracts=tuple(contracts),
            )
        except OptionChainProviderError:
            raise
        except (KeyError, TypeError, ValueError, ArithmeticError) as exc:
            raise OptionChainProviderError("Dhan returned malformed option-chain data") from exc
