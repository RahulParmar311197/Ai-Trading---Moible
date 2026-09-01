"""Deterministic structured market context for AI consumers.

The builder derives every fact from the candles supplied by the caller. A replay
caller can therefore pass only candles visible at replay time T, preserving the
blueprint's no-look-ahead rule.
"""

from decimal import Decimal
from typing import Any, Mapping

from app.market.models import Candle
from app.smc.engine import SmcAnalysis, SmcEngine
from app.smc.sessions import ICT_LONDON, ICT_NEW_YORK, in_window, session_levels

from .contracts import AIAnalysisRequest


class MarketContextBuilder:
    """Build a provider-neutral AIAnalysisRequest from deterministic market facts."""

    def __init__(self, smc: SmcEngine | None = None) -> None:
        self.smc = smc or SmcEngine()

    def build(
        self,
        candles: list[Candle],
        *,
        risk_context: Mapping[str, Any] | None = None,
        options_context: Mapping[str, Any] | None = None,
        strategy_context: Mapping[str, Any] | None = None,
    ) -> AIAnalysisRequest:
        if not candles:
            raise ValueError("at least one visible candle is required")
        visible = list(candles)
        current = visible[-1]
        analysis = self.smc.analyze(visible)
        return self.from_analysis(
            visible,
            analysis,
            risk_context=risk_context,
            options_context=options_context,
            strategy_context=strategy_context,
        )

    def from_analysis(
        self,
        candles: list[Candle],
        analysis: SmcAnalysis,
        *,
        risk_context: Mapping[str, Any] | None = None,
        options_context: Mapping[str, Any] | None = None,
        strategy_context: Mapping[str, Any] | None = None,
    ) -> AIAnalysisRequest:
        if not candles:
            raise ValueError("at least one visible candle is required")
        current = candles[-1]
        latest_sweep = max(analysis.liquidity_sweeps, key=lambda item: (item.timestamp, item.candle_index), default=None)
        latest_fvg = max(analysis.fvgs, key=lambda item: (item.created_at, item.candle_index), default=None)
        latest_structure = max(analysis.structure, key=lambda item: item.timestamp, default=None)
        market_range = current.high - current.low
        body = abs(current.close - current.open)

        london = session_levels(candles, ICT_LONDON)
        new_york = session_levels(candles, ICT_NEW_YORK)
        active_sessions = [window.name for window in (ICT_LONDON, ICT_NEW_YORK) if in_window(current.timestamp, window)]

        smc_context = {
            "signal": analysis.signal.model_dump(mode="json"),
            "swing_count": len(analysis.swings),
            "structure_count": len(analysis.structure),
            "liquidity_pool_count": len(analysis.liquidity_pools),
            "liquidity_sweep_count": len(analysis.liquidity_sweeps),
            "fvg_count": len(analysis.fvgs),
            "order_block_count": len(analysis.order_blocks),
            "current_zone": analysis.current_zone,
            "latest_structure": latest_structure.model_dump(mode="json") if latest_structure else None,
            "latest_sweep": latest_sweep.model_dump(mode="json") if latest_sweep else None,
            "latest_fvg": latest_fvg.model_dump(mode="json") if latest_fvg else None,
        }
        ict_context = {
            "active_sessions": active_sessions,
            "london_levels": london.model_dump(mode="json") if london else None,
            "new_york_levels": new_york.model_dump(mode="json") if new_york else None,
        }
        technical_context = {
            "candle_count": len(candles),
            "range": market_range,
            "body": body,
            "body_to_range": (body / market_range if market_range else Decimal("0")),
            "volume": current.volume,
        }
        return AIAnalysisRequest(
            symbol=current.instrument_id,
            timeframe=current.timeframe,
            market_context={
                "timestamp": current.timestamp,
                "open": current.open,
                "high": current.high,
                "low": current.low,
                "close": current.close,
                "volume": current.volume,
            },
            smc_context=smc_context,
            ict_context=ict_context,
            technical_context=technical_context,
            options_context=dict(options_context or {}),
            risk_context=dict(risk_context or {}),
            strategy_context=dict(strategy_context or {}),
        )
