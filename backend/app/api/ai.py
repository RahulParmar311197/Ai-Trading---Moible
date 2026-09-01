"""Structured AI API endpoints with an explicit provider configuration gate."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ai.contracts import AIAnalysisRequest, AIAnalysisResponse
from app.ai.provider import AIProviderError, HttpAIProvider
from app.ai.service import AIService
from app.config import settings

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


class AIStrategyRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    context: AIAnalysisRequest


class AIExplainTradeRequest(BaseModel):
    proposal: dict[str, Any]
    context: AIAnalysisRequest


def _service() -> AIService:
    if not settings.ai_provider_url:
        raise HTTPException(status_code=503, detail="AI provider is not configured")
    return AIService(
        HttpAIProvider(
            settings.ai_provider_url,
            api_key=settings.ai_provider_api_key,
            model=settings.ai_provider_model,
            timeout=settings.ai_provider_timeout_seconds,
        )
    )


@router.post("/analyze", response_model=AIAnalysisResponse)
def analyze(request: AIAnalysisRequest) -> AIAnalysisResponse:
    try:
        return _service().analyze(request)
    except AIProviderError as exc:
        raise HTTPException(status_code=502, detail="AI provider unavailable") from exc
    except ValueError as exc:
        raise HTTPException(status_code=502, detail="AI provider returned invalid analysis") from exc


@router.post("/strategy")
def generate_strategy(request: AIStrategyRequest) -> dict[str, Any]:
    try:
        strategy = _service().generate_strategy(request.prompt, request.context)
    except AIProviderError as exc:
        raise HTTPException(status_code=502, detail="AI provider unavailable") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"strategy": strategy.model_dump(mode="json")}


@router.post("/explain-trade")
def explain_trade(request: AIExplainTradeRequest) -> dict[str, str]:
    try:
        summary = _service().explain_trade(request.proposal, request.context)
    except AIProviderError as exc:
        raise HTTPException(status_code=502, detail="AI provider unavailable") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"summary": summary}
