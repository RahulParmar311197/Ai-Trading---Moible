"""Concrete Upstox protobuf decoder adapter.

The generated ``MarketDataFeedV3_pb2`` module is intentionally supplied by the
official Upstox SDK/dependency rather than copied or hand-written here.
"""

from app.market.upstox_proto import UpstoxProtoDecoder


def decode_upstox_feed(payload: bytes) -> object:
    try:
        from upstox_client.feeder.market_data_feed_v3_pb2 import FeedResponse
    except ImportError as exc:
        raise RuntimeError(
            "Install the official Upstox SDK protobuf module before enabling live feed"
        ) from exc

    response = FeedResponse()
    response.ParseFromString(payload)
    return response


def create_upstox_decoder() -> UpstoxProtoDecoder:
    return UpstoxProtoDecoder(decode_upstox_feed)
