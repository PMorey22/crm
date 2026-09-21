from poc20.domain.models import LeadScore, Requirements


class LeadScorer:
    """
    Deterministic lead qualification scorer.

    The score is based on completeness and buying intent,
    not on an LLM-generated number.
    """

    def calculate(
        self,
        requirements: Requirements,
    ) -> LeadScore:
        score = 0.0
        reasons: list[str] = []

        # Location
        if requirements.location:
            score += 25
            reasons.append("Location provided")

        # Budget
        if requirements.budget_lakhs is not None:
            score += 25
            reasons.append("Budget provided")

        # Property requirements
        if (
            requirements.bedrooms is not None
            or requirements.property_type is not None
        ):
            score += 20
            reasons.append("Property requirements provided")

        # Timeline
        if requirements.timeline_months is not None:
            score += 20
            reasons.append("Purchase timeline provided")

            if requirements.timeline_months <= 3:
                score += 10
                reasons.append(
                    "Short purchase timeline indicates stronger intent"
                )

        return LeadScore(
            score=min(score, 100),
            reasons=reasons,
        )