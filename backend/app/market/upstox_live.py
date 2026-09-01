"""Upstox V3 live-feed transport boundary.

Upstox V3 requires an authorized WebSocket and binary Protobuf messages. This
module owns authorization, subscription framing, and decoded-message injection;
the generated official protobuf type is deliberately injected so the core
market engine remains independent of the provider schema.
"""

import json
from collections.abc import AsyncIterator, Callable
from typing import Any

import httpx
import websockets


class UpstoxLiveConfigurationError(RuntimeError):
    pass


class UpstoxLiveFeed:
    AUTHORIZE_URL = "https://api.upstox.com/v3/feed/market-data-feed/authorize"

    def __init__(self, access_token: str, decoder: Callable[[bytes], Any]) -> None:
        if not access_token.strip():
            raise UpstoxLiveConfigurationError("UPSTOX_ACCESS_TOKEN is required")
        self.access_token = access_token
        self.decoder = decoder

    async def authorize(self) -> str:
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(self.AUTHORIZE_URL, headers=headers)
            response.raise_for_status()
            payload = response.json()
        try:
            return payload["data"]["authorized_redirect_uri"]
        except KeyError as exc:
            raise UpstoxLiveConfigurationError("Upstox authorization response has no websocket URI") from exc

    async def stream(self, instrument_keys: list[str], mode: str = "ltpc") -> AsyncIterator[Any]:
        uri = await self.authorize()
        async with websockets.connect(uri, origin=None) as socket:
            subscription = {
                "guid": "ai-trading-platform",
                "method": "sub",
                "data": {"mode": mode, "instrumentKeys": instrument_keys},
            }
            await socket.send(json.dumps(subscription).encode("utf-8"))
            async for payload in socket:
                if isinstance(payload, str):
                    payload = payload.encode("utf-8")
                yield self.decoder(payload)
