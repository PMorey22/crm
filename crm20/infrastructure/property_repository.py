import csv
import json
from pathlib import Path
from typing import Any


class PropertyRepository:
    """
    Loads property inventory from JSON or CSV.

    The repository keeps the property source separate from
    the matching and workflow layers.
    """

    def __init__(
        self,
        json_path: str = "properties.json",
        csv_path: str = "properties.csv",
    ):
        self.json_path = Path(json_path)
        self.csv_path = Path(csv_path)

    def get_all(self) -> list[dict[str, Any]]:
        if self.json_path.exists():
            return self._load_json()

        if self.csv_path.exists():
            return self._load_csv()

        return []

    def get_by_id(
        self,
        property_id: str,
    ) -> dict[str, Any] | None:
        for property_data in self.get_all():
            current_id = str(
                property_data.get("property_id")
                or property_data.get("id")
                or ""
            )

            if current_id == property_id:
                return property_data

        return None

    def _load_json(self) -> list[dict[str, Any]]:
        with self.json_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if isinstance(data, dict):
            if "properties" in data:
                data = data["properties"]
            else:
                data = [data]

        if not isinstance(data, list):
            raise ValueError(
                "Property JSON must contain a list of properties."
            )

        return [
            item
            for item in data
            if isinstance(item, dict)
        ]

    def _load_csv(self) -> list[dict[str, Any]]:
        with self.csv_path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.DictReader(file)

            return [
                dict(row)
                for row in reader
            ]