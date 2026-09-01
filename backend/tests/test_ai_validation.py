from decimal import Decimal

import pytest

from app.ai.contracts import AITradeProposal
from app.ai.validation import AIOutputValidator


def proposal(**overrides):
    values = {
        "direction": "LONG",
        "entry": "100",
        "stop": "95",
        "target": "110",
        "risk_reward": "2",
        "setup_score": 80,
        "conditions_satisfied": ("liquidity_sweep", "bullish_mss", "bullish_fvg"),
    }
    values.update(overrides)
    return AITradeProposal(**values)


def test_ai_proposal_is_accepted_only_when_deterministic_facts_match():
    result = AIOutputValidator().validate(
        proposal(),
        signal_exists=True,
        expected_direction="LONG",
        deterministic_score=85,
        minimum_rr=Decimal("1.5"),
        required_conditions={"liquidity_sweep", "bullish_mss", "bullish_fvg"},
    )
    assert result.direction == "LONG"


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"signal_exists": False}, "no deterministic signal"),
        ({"signal_exists": True, "expected_direction": "SHORT"}, "direction"),
        ({"signal_exists": True, "deterministic_score": 70}, "setup score"),
        ({"signal_exists": True, "minimum_rr": Decimal("3")}, "risk/reward"),
        ({"signal_exists": True, "required_conditions": {"order_block"}}, "required conditions"),
    ],
)
def test_ai_proposal_rejection_gates(kwargs, message):
    with pytest.raises(ValueError, match=message):
        AIOutputValidator().validate(proposal(), **kwargs)


def test_ai_proposal_cannot_claim_an_inconsistent_risk_reward():
    with pytest.raises(ValueError, match="does not match prices"):
        AIOutputValidator().validate(
            proposal(risk_reward=Decimal("3")),
            signal_exists=True,
        )


def test_ai_proposal_rejects_zero_entry_stop_distance():
    with pytest.raises(ValueError, match="entry and stop"):
        AIOutputValidator().validate(
            proposal(entry=Decimal("100"), stop=Decimal("100"), target=Decimal("110"), risk_reward=Decimal("2")),
            signal_exists=True,
        )
