import re
from dataclasses import dataclass
from typing import Any

from poc20.domain.models import PropertyMatch, Requirements


@dataclass
class NormalizedProperty:
    property_id: str
    location: str
    property_type: str | None
    bedrooms: int | None
    price_lakhs: float | None
    raw: dict[str, Any]


class PropertyMatcher:
    """
    Deterministic property matching and ranking service.

    Property data is normalized once when the matcher is created.
    """

    def __init__(self, properties: list[dict[str, Any]]):
        self.properties = [
            self._normalize_property(property_data)
            for property_data in properties
        ]

    def find_matches(
        self,
        requirements: Requirements,
        limit: int = 5,
    ) -> list[PropertyMatch]:
        if limit <= 0:
            return []

        candidates: list[PropertyMatch] = []

        for property_data in self.properties:
            score, reasons = self._calculate_score(
                property_data,
                requirements,
            )

            if score > 0:
                candidates.append(
                    PropertyMatch(
                        property_id=property_data.property_id,
                        score=round(score, 2),
                        reasons=reasons,
                    )
                )

        candidates.sort(
            key=lambda match: match.score,
            reverse=True,
        )

        return candidates[:limit]

    def _calculate_score(
        self,
        property_data: NormalizedProperty,
        requirements: Requirements,
    ) -> tuple[float, list[str]]:
        score = 0.0
        reasons: list[str] = []

        # Location = 40%
        if requirements.location:
            requested_location = self._normalize_text(
                requirements.location
            )

            property_location = self._normalize_text(
                property_data.location
            )

            if (
                requested_location in property_location
                or property_location in requested_location
            ):
                score += 40
                reasons.append(
                    f"Location matched: {property_data.location}"
                )
            else:
                return 0.0, []

        # Bedrooms = 25%
        if requirements.bedrooms is not None:
            if property_data.bedrooms == requirements.bedrooms:
                score += 25
                reasons.append(
                    f"Bedroom count matched: "
                    f"{requirements.bedrooms}BHK"
                )
            else:
                return 0.0, []

        # Budget = 25%
        if requirements.budget_lakhs is not None:
            if property_data.price_lakhs is None:
                return 0.0, []

            if property_data.price_lakhs <= requirements.budget_lakhs:
                score += 25
                reasons.append(
                    f"Price matched: "
                    f"₹{property_data.price_lakhs:g} lakh "
                    f"<= ₹{requirements.budget_lakhs:g} lakh budget"
                )
            else:
                return 0.0, []

        # Property type = 10%
        if requirements.property_type is not None:
            requested_type = requirements.property_type.value

            if (
                property_data.property_type
                == requested_type
            ):
                score += 10
                reasons.append(
                    f"Property type matched: {requested_type}"
                )

        return score, reasons

    @staticmethod
    def _normalize_property(
        property_data: dict[str, Any],
    ) -> NormalizedProperty:
        property_id = str(
            property_data.get("property_id")
            or property_data.get("id")
            or ""
        )

        location = str(
            property_data.get("location")
            or property_data.get("city")
            or ""
        )

        property_type = property_data.get(
            "property_type"
        )

        bedrooms = PropertyMatcher._parse_bedrooms(
            property_data.get("bedrooms")
            or property_data.get("property_type")
            or property_data.get("bhk")
        )

        price_lakhs = PropertyMatcher._parse_price(
            property_data.get("price_lakhs")
            or property_data.get("price")
            or property_data.get("budget")
        )

        return NormalizedProperty(
            property_id=property_id,
            location=location,
            property_type=(
                str(property_type).upper()
                if property_type
                else None
            ),
            bedrooms=bedrooms,
            price_lakhs=price_lakhs,
            raw=property_data,
        )

    @staticmethod
    def _parse_bedrooms(value: Any) -> int | None:
        if value is None:
            return None

        if isinstance(value, int):
            return value

        match = re.search(
            r"(\d+)\s*(?:BHK|BEDROOM)",
            str(value),
            re.IGNORECASE,
        )

        if match:
            return int(match.group(1))

        return None

    @staticmethod
    def _parse_price(value: Any) -> float | None:
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip().lower()

        crore_match = re.search(
            r"([\d.]+)\s*(?:crore|cr)",
            text,
        )

        if crore_match:
            return float(crore_match.group(1)) * 100

        lakh_match = re.search(
            r"([\d.]+)\s*(?:lakh|lac|l)",
            text,
        )

        if lakh_match:
            return float(lakh_match.group(1))

        number_match = re.search(
            r"[\d.]+",
            text,
        )

        if number_match:
            return float(number_match.group())

        return None

    @staticmethod
    def _normalize_text(value: str) -> str:
        return re.sub(
            r"\s+",
            " ",
            re.sub(
                r"[^a-z0-9 ]",
                " ",
                value.lower(),
            ),
        ).strip()