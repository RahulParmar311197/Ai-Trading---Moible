from decimal import Decimal

import pytest

from app.ai.contracts import AIAnalysisRequest
from app.ai.provider import AIProviderError, HttpAIProvider
from app.ai.service import AIService
from app.market.models import Timeframe


class FakeProvider:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def complete(self, *, system, payload):
        self.calls.append((system, payload))
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def context():
    return AIAnalysisRequest(symbol="NIFTY", timeframe=Timeframe.M15, market_context={"close": Decimal("25000")})


def test_ai_service_analyze_validates_provider_output():
    provider = FakeProvider({"summary": "Bullish structure", "proposal": None})
    result = AIService(provider).analyze(context())
    assert result.summary == "Bullish structure"
    assert provider.calls
    assert provider.calls[0][1]["symbol"] == "NIFTY"


def test_ai_service_strategy_uses_strict_dsl_translation():
    provider = FakeProvider(
        {
            "name": "Bullish Sweep",
            "market": "NIFTY",
            "timeframe": "15m",
            "direction": "bullish",
            "conditions": [{"type": "mss", "field": "bias", "value": "BULLISH"}],
            "entry": {"stop_distance": "10"},
            "risk": {"risk_percent": "0.5", "minimum_rr": "2"},
        }
    )
    strategy = AIService(provider).generate_strategy("find a bullish MSS", context())
    assert strategy.name == "Bullish Sweep"


def test_ai_service_explain_trade_requires_summary():
    provider = FakeProvider({"summary": "Setup satisfies the supplied deterministic facts."})
    result = AIService(provider).explain_trade({"direction": "LONG"}, context())
    assert result.startswith("Setup satisfies")


def test_ai_service_propagates_provider_failure():
    provider = FakeProvider(AIProviderError("offline"))
    with pytest.raises(AIProviderError):
        AIService(provider).analyze(context())


def test_http_provider_requires_endpoint():
    with pytest.raises(ValueError, match="endpoint"):
        HttpAIProvider("")
