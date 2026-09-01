from app.market.upstox_normalizer import normalize_upstox_feed_response


class Obj:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_normalize_official_ltpc_shape():
    response = Obj(feeds={"NSE_EQ|TEST": Obj(ltpc=Obj(ltp=100.5, ltt="1740729552723", ltq="7"))})
    events = normalize_upstox_feed_response(response)
    assert len(events) == 1
    assert str(events[0].close) == "100.5"
    assert str(events[0].volume) == "7"


def test_normalize_full_market_feed_shape():
    response = Obj(feeds={"NSE_INDEX|Nifty 50": Obj(ff=Obj(indexFF=Obj(ltpc=Obj(ltp=24936.4, ltt="1725877800000", ltq="1"))))})
    events = normalize_upstox_feed_response(response)
    assert len(events) == 1
    assert events[0].instrument_id == "NSE_INDEX|Nifty 50"
