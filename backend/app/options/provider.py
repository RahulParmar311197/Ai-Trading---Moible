from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from .models import OptionChain


class OptionChainProvider(ABC):
    """Provider-neutral boundary for live option-chain data."""

    @abstractmethod
    async def get_option_chain(self, underlying: str, expiry: date | None = None) -> OptionChain:
        raise NotImplementedError


class UnconfiguredOptionChainProvider(OptionChainProvider):
    """Safe default: live options remain unavailable until a provider is configured."""

    async def get_option_chain(self, underlying: str, expiry: date | None = None) -> OptionChain:
        raise RuntimeError("live option-chain provider is not configured")
