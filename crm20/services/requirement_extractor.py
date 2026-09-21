import json
import logging
from typing import Any, Protocol

from pydantic import ValidationError

from poc20.domain.models import Requirements


logger = logging.getLogger(__name__)


class LLMClient(Protocol):
    def complete(
        self,
        system_prompt: str,
        user_message: str,
    ) -> str:
        ...


class RequirementExtractionError(Exception):
    """Raised when lead requirements cannot be extracted."""


class RequirementExtractor:
    """
    Converts natural-language lead messages into
    validated Requirements objects.
    """

    SYSTEM_PROMPT = """
You are a real-estate lead qualification assistant.

Extract only information explicitly provided by the user.

Return a JSON object with exactly these fields:

{
    "location": string or null,
    "property_type": "APARTMENT" | "VILLA" | "PLOT" | "HOUSE" | null,
    "bedrooms": integer or null,
    "budget_lakhs": number or null,
    "timeline_months": integer or null
}

Rules:

1. Never invent missing information.
2. "80 lakhs" means 80.
3. "80L" means 80.
4. "1 crore" means 100 lakhs.
5. "1.2 crore" means 120 lakhs.
6. "2 BHK" means bedrooms = 2.
7. If the user says BHK but does not specify another
   property type, use property_type = "APARTMENT".
8. If a field is not present, return null.
9. timeline_months must be an integer.
"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def extract(
        self,
        message: str,
    ) -> Requirements:

        if not message or not message.strip():
            raise RequirementExtractionError(
                "Message cannot be empty."
            )

        try:
            response = self.llm_client.complete(
                system_prompt=self.SYSTEM_PROMPT,
                user_message=message,
            )

            data = self._parse_response(response)

            return Requirements.model_validate(data)

        except ValidationError as exc:
            logger.warning(
                "Requirement validation failed: %s",
                exc,
            )

            raise RequirementExtractionError(
                "Extracted requirements failed validation."
            ) from exc

        except RequirementExtractionError:
            raise

        except Exception as exc:
            logger.exception(
                "Requirement extraction failed."
            )

            raise RequirementExtractionError(
                "Unable to extract requirements."
            ) from exc

    @staticmethod
    def _parse_response(
        response: Any,
    ) -> dict[str, Any]:

        if isinstance(response, dict):
            return response

        if not isinstance(response, str):
            raise RequirementExtractionError(
                "LLM response must be a JSON string."
            )

        try:
            data = json.loads(response)

        except json.JSONDecodeError as exc:
            raise RequirementExtractionError(
                "LLM returned invalid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise RequirementExtractionError(
                "LLM response must be a JSON object."
            )

        return data