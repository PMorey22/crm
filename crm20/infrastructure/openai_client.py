import logging
from typing import Any

from openai import OpenAI

from poc20.config import get_settings


logger = logging.getLogger(__name__)


class OpenAIClientError(Exception):
    """Raised when communication with OpenAI fails."""


class OpenAIClient:
    """
    Thin wrapper around the OpenAI SDK.

    The rest of the application does not directly depend
    on the OpenAI SDK.
    """

    def __init__(
        self,
        client: OpenAI | None = None,
    ):
        settings = get_settings()

        if client is not None:
            self.client = client
        else:
            if not settings.openai_api_key:
                raise OpenAIClientError(
                    "OPENAI_API_KEY is not configured."
                )

            self.client = OpenAI(
                api_key=settings.openai_api_key,
            )

        self.model = settings.openai_model

    def complete(
        self,
        system_prompt: str,
        user_message: str,
    ) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_message,
                    },
                ],
                temperature=0,
                response_format={
                    "type": "json_object",
                },
            )

            content = response.choices[0].message.content

            if not content:
                raise OpenAIClientError(
                    "OpenAI returned an empty response."
                )

            return content

        except OpenAIClientError:
            raise

        except Exception as exc:
            logger.exception(
                "OpenAI request failed."
            )

            raise OpenAIClientError(
                "Unable to communicate with OpenAI."
            ) from exc