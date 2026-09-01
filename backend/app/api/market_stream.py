"""WebSocket market-stream endpoint.

The endpoint is transport-only: provider adapters publish normalized events to
an in-process hub, while Redis fan-out will be introduced in the next stage.
No synthetic market data is generated.
"""

import asyncio
import json
from collections import defaultdict
from collections.abc import AsyncIterator

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.market.models import MarketEvent

router = APIRouter(prefix="/api/v1/market-data", tags=["market-data"])


class MarketEventHub:
    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue[str]]] = defaultdict(set)

    async def subscribe(self, instrument_id: str) -> AsyncIterator[str]:
        queue: asyncio.Queue[str] = asyncio.Queue()
        subscribers = self._subscribers[instrument_id]
        subscribers.add(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            subscribers.discard(queue)
            if not subscribers:
                self._subscribers.pop(instrument_id, None)

    async def publish(self, event: MarketEvent) -> None:
        payload = event.model_dump_json()
        for queue in tuple(self._subscribers.get(event.instrument_id, ())):
            await queue.put(payload)


market_event_hub = MarketEventHub()


@router.websocket("/stream/{instrument_id}")
async def market_stream(websocket: WebSocket, instrument_id: str) -> None:
    await websocket.accept()
    try:
        async for payload in market_event_hub.subscribe(instrument_id):
            await websocket.send_text(payload)
    except WebSocketDisconnect:
        return
