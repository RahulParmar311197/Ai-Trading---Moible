import pytest

from app.market.upstox_proto import UpstoxProtoDecoder


def test_decoder_delegates_binary_payload():
    decoder = UpstoxProtoDecoder(lambda payload: {"payload": payload})
    assert decoder.decode(b"wire") == {"payload": b"wire"}


def test_decoder_rejects_empty_payload():
    decoder = UpstoxProtoDecoder(lambda payload: payload)
    with pytest.raises(ValueError, match="empty"):
        decoder.decode(b"")
