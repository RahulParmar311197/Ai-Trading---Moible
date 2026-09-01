from datetime import datetime, time, timezone
from decimal import Decimal

import pytest

from app.ai.context import MarketContextBuilder
from app.ai.translator import StrategyDslTranslationError, StrategyDslTranslator
from app.market.models import Candle, Timeframe
from app.smc.engine import SmcEngine
from app.smc.models import Bias, SignalContext


def candle(i: int, close: str = "100") -> Candle:
    price = Decimal(close)
    return Candle(
        instrument_id="NIFTY",
        timestamp=datetime(2026, 1, 1, 7, 15 + i, tzinfo=timezone.utc),
        timeframe=Timeframe.M1,
        open=price,
        high=price + 5,
        low=price - 5,
        close=price,
        volume=Decimal("100"),
    )


def test_market_context_contains_only_visible_market_and_smc_facts():
    visible = [candle(0), candle(1)]
    request = MarketContextBuilder(SmcEngine()).build(visible, risk_context={"risk_percent": Decimal("0.5")})

    assert request.symbol == "NIFTY"
    assert request.timeframe is Timeframe.M1
    assert request.market_context["close"] == Decimal("100")
    assert request.technical_context["candle_count"] == 2
    assert request.risk_context["risk_percent"] == Decimal("0.5")
    assert "signal" in request.smc_context
    assert "active_sessions" in request.ict_context


def test_market_context_rejects_empty_visible_history():
    with pytest.raises(ValueError, match="visible candle"):
        MarketContextBuilder().build([])


def test_market_context_can_project_an_existing_deterministic_analysis():
    visible = [candle(0)]
    analysis = SmcEngine().analyze(visible)
    request = MarketContextBuilder().from_analysis(visible, analysis)
    assert request.smc_context["signal"]["bias"] == Bias.NEUTRAL.value


def valid_strategy() -> dict[str, object]:
    return {
        "name": "Bullish Sweep",
        "market": "NIFTY",
        "timeframe": "1m",
        "direction": "bullish",
        "conditions": [
            {"type": "mss", "field": "bias", "value": "BULLISH"},
            {"type": "fvg"},
        ],
        "entry": {"stop_distance": "5"},
        "risk": {"risk_percent": "0.5", "minimum_rr": "2"},
    }


def test_ai_translation_validates_declarative_strategy_payload():
    strategy = StrategyDslTranslator().translate(valid_strategy())
    assert strategy.name == "Bullish Sweep"
    assert strategy.risk.risk_percent == Decimal("0.5")


def test_ai_translation_accepts_json_string():
    import json

    strategy = StrategyDslTranslator().translate(json.dumps(valid_strategy()))
    assert strategy.timeframe is Timeframe.M1


@pytest.mark.parametrize("key", ["python", "code", "exec", "place_order", "broker_order"])
def test_ai_translation_rejects_executable_output(key):
    payload = valid_strategy()
    payload[key] = "do something unsafe"
    with pytest.raises(StrategyDslTranslationError, match="executable field rejected"):
        StrategyDslTranslator().translate(payload)


def test_ai_translation_rejects_invalid_strategy_shape():
    payload = valid_strategy()
    payload["risk"] = {"risk_percent": "0"}
    with pytest.raises(StrategyDslTranslationError, match="failed DSL validation"):
        StrategyDslTranslator().translate(payload)
