"""Safe AI orchestration over structured market facts."""

from collections.abc import Mapping
from typing import Any

from .contracts import AIAnalysisRequest, AIAnalysisResponse
from .provider import AIProvider
from .translator import StrategyDslTranslator

_SYSTEM = (
    "You are an analysis assistant for a trading platform. Use only the supplied structured facts. "
    "Do not invent market data. AI output is advisory and never authorizes an order. "
    "Return JSON only when requested."
)


class AIService:
    def __init__(self, provider: AIProvider, translator: StrategyDslTranslator | None = None) -> None:
        self.provider = provider
        self.translator = translator or StrategyDslTranslator()

    def analyze(self, request: AIAnalysisRequest) -> AIAnalysisResponse:
        result = self.provider.complete(system=_SYSTEM, payload=request.model_dump(mode="json"))
        return AIAnalysisResponse.model_validate(result)

    def generate_strategy(self, prompt: str, context: AIAnalysisRequest) -> Any:
        if not prompt.strip():
            raise ValueError("strategy prompt must not be empty")
        result = self.provider.complete(
            system=(
                f"{_SYSTEM} Translate the user's request into the declarative StrategyDefinition schema. "
                "Never return executable code, broker commands, or order instructions."
            ),
            payload={"prompt": prompt, "context": context.model_dump(mode="json")},
        )
        return self.translator.translate(result)

    def explain_trade(self, proposal: Mapping[str, Any], context: AIAnalysisRequest) -> str:
        result = self.provider.complete(
            system=(
                f"{_SYSTEM} Explain the supplied deterministic trade proposal. "
                "Do not increase its confidence or invent missing facts."
            ),
            payload={"proposal": dict(proposal), "context": context.model_dump(mode="json")},
        )
        summary = result.get("summary") if isinstance(result, Mapping) else None
        if not isinstance(summary, str) or not summary.strip():
            raise ValueError("AI explanation response must contain a non-empty summary")
        return summary
