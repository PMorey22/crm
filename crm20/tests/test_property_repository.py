import json

from poc20.infrastructure.property_repository import (
    PropertyRepository,
)


def test_load_properties_from_json(
    tmp_path,
) -> None:
    file_path = tmp_path / "properties.json"

    file_path.write_text(
        json.dumps(
            [
                {
                    "property_id": "P1",
                    "location": "Hinjewadi",
                    "bedrooms": 2,
                }
            ]
        ),
        encoding="utf-8",
    )

    repository = PropertyRepository(
        json_path=str(file_path),
        csv_path=str(
            tmp_path / "properties.csv"
        ),
    )

    properties = repository.get_all()

    assert len(properties) == 1
    assert properties[0]["property_id"] == "P1"


def test_get_property_by_id(
    tmp_path,
) -> None:
    file_path = tmp_path / "properties.json"

    file_path.write_text(
        json.dumps(
            [
                {
                    "property_id": "P1",
                    "location": "Wakad",
                }
            ]
        ),
        encoding="utf-8",
    )

    repository = PropertyRepository(
        json_path=str(file_path)
    )

    result = repository.get_by_id("P1")

    assert result is not None
    assert result["location"] == "Wakad"