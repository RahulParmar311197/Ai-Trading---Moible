"""Upstox V3 Protobuf decoding boundary.

The official Upstox SDK exposes MarketDataFeedV3.FeedResponse as the wire
message. The application keeps the generated schema outside the core market
models and injects a decoder so the transport remains testable.
"""

from collections.abc import Callable


class UpstoxProtoDecoder:
    def __init__(self, parser: Callable[[bytes], object]) -> None:
        self._parser = parser

    def decode(self, payload: bytes) -> object:
        if not payload:
            raise ValueError("Upstox feed payload cannot be empty")
        return self._parser(payload)
