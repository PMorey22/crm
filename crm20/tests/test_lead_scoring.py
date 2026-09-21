from poc20.domain.models import Requirements
from poc20.services.lead_scorer import LeadScorer


def test_high_intent_lead_score() -> None:
    requirements = Requirements(
        location="Hinjewadi",
        bedrooms=2,
        budget_lakhs=80,
        timeline_months=2,
    )

    score = LeadScorer().calculate(
        requirements
    )

    assert score.score == 100
    assert "Location provided" in score.reasons
    assert "Budget provided" in score.reasons
    assert (
        "Short purchase timeline indicates stronger intent"
        in score.reasons
    )


def test_partial_lead_score() -> None:
    requirements = Requirements(
        location="Wakad"
    )

    score = LeadScorer().calculate(
        requirements
    )

    assert score.score == 25