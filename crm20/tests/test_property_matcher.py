from poc20.domain.models import Requirements
from poc20.services.property_matcher import (
    PropertyMatcher,
)


def test_property_matching() -> None:
    properties = [
        {
            "property_id": "P1",
            "location": "Hinjewadi",
            "property_type": "APARTMENT",
            "bedrooms": 2,
            "price_lakhs": 78,
        },
        {
            "property_id": "P2",
            "location": "Hinjewadi",
            "property_type": "APARTMENT",
            "bedrooms": 3,
            "price_lakhs": 95,
        },
        {
            "property_id": "P3",
            "location": "Wakad",
            "property_type": "APARTMENT",
            "bedrooms": 2,
            "price_lakhs": 75,
        },
    ]

    matcher = PropertyMatcher(properties)

    requirements = Requirements(
        location="Hinjewadi",
        property_type="APARTMENT",
        bedrooms=2,
        budget_lakhs=80,
    )

    matches = matcher.find_matches(
        requirements
    )

    assert len(matches) == 1
    assert matches[0].property_id == "P1"
    assert matches[0].score == 100