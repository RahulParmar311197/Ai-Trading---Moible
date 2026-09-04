"""Deterministic validation of AI output before any downstream execution."""

from decimal import Decimal

from app.ai.contracts import AITradeProposal


class AIOutputValidator:
    """Validate AI suggestions against deterministic facts and strategy constraints."""

    def validate(
        self,
        proposal: AITradeProposal,
        *,
        signal_exists: bool,
        expected_direction: str | None = None,
        deterministic_score: int | None = None,
        minimum_rr: Decimal | None = None,
        required_conditions: set[str] | None = None,
    ) -> AITradeProposal:
        if not signal_exists:
            raise ValueError("AI proposal rejected: no deterministic signal exists")
        if expected_direction is not None and proposal.direction != expected_direction:
            raise ValueError("AI proposal rejected: direction does not match deterministic signal")
        if deterministic_score is not None and proposal.setup_score > deterministic_score:
            raise ValueError("AI proposal rejected: setup score exceeds deterministic score")
        if minimum_rr is not None and proposal.risk_reward < minimum_rr:
            raise ValueError("AI proposal rejected: risk/reward is below strategy minimum")
        if required_conditions:
            missing = required_conditions.difference(proposal.conditions_satisfied)
            if missing:
                raise ValueError("AI proposal rejected: required conditions are not satisfied")

        distance = abs(proposal.entry - proposal.stop)
        if distance == 0:
            raise ValueError("AI proposal rejected: entry and stop must differ")

        if proposal.direction == "LONG":
            if not proposal.stop < proposal.entry < proposal.target:
                raise ValueError("AI proposal rejected: LONG requires stop < entry < target")
        elif not proposal.target < proposal.entry < proposal.stop:
            raise ValueError("AI proposal rejected: SHORT requires target < entry < stop")

        expected_rr = abs(proposal.target - proposal.entry) / distance
        if abs(expected_rr - proposal.risk_reward) > Decimal("0.000001"):
            raise ValueError("AI proposal rejected: risk/reward does not match prices")
        return proposal
