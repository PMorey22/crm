from poc20.services.requirement_extractor import (
    RequirementExtractor,
)


class FakeLLMClient:
    def complete(
        self,
        system_prompt: str,
        user_message: str,
    ) -> str:
        return """
        {
            "location": "Hinjewadi",
            "property_type": "APARTMENT",
            "bedrooms": 2,
            "budget_lakhs": 80,
            "timeline_months": 3
        }
        """


def test_requirement_extraction() -> None:
    extractor = RequirementExtractor(
        llm_client=FakeLLMClient()
    )

    result = extractor.extract(
        "I need a 2BHK in Hinjewadi for 80L "
        "and want to move in within 3 months."
    )

    assert result.location == "Hinjewadi"
    assert result.bedrooms == 2
    assert result.budget_lakhs == 80
    assert result.timeline_months == 3