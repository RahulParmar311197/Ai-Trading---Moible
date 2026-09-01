"""Concrete Upstox protobuf decoder adapter.

The generated ``MarketDataFeedV3_pb2`` module is supplied by the official
Upstox Python SDK. The SDK currently exposes it under ``upstox_client.feeder.proto``.
"""

from app.market.upstox_proto import UpstoxProtoDecoder


def decode_upstox_feed(payload: bytes) -> object:
    try:
        from upstox_client.feeder.proto import MarketDataFeedV3_pb2
    except ImportError as exc:
        raise RuntimeError(
            "Install the official Upstox SDK protobuf module before enabling live feed"
        ) from exc

    return MarketDataFeedV3_pb2.FeedResponse.FromString(payload)


def create_upstox_decoder() -> UpstoxProtoDecoder:
    return UpstoxProtoDecoder(decode_upstox_feed)
