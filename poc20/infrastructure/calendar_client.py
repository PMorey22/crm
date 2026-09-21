from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import hashlib
import logging

from sqlalchemy.orm import Session

from poc20.domain.exceptions import ExternalServiceError
from poc20.infrastructure.repositories import IdempotencyRepository


logger = logging.getLogger(__name__)


@dataclass
class CalendarEvent:
    event_id: str
    title: str
    start_time: datetime
    end_time: datetime
    timezone: str
    property_id: str | None = None
    session_id: str | None = None


class CalendarClient(ABC):
    """Interface for calendar providers."""

    @abstractmethod
    def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        timezone: str,
        property_id: str | None = None,
        session_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> CalendarEvent:
        raise NotImplementedError


class MockCalendarClient(CalendarClient):
    """
    Local calendar implementation for the POC.

    No external calendar credentials are required.
    Events are stored in memory while the application runs.
    """

    def __init__(
        self,
        db: Session | None = None,
    ):
        self.events: dict[str, CalendarEvent] = {}

        self.idempotency_repository = (
            IdempotencyRepository(db)
            if db is not None
            else None
        )

    def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        timezone: str,
        property_id: str | None = None,
        session_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> CalendarEvent:

        if end_time <= start_time:
            raise ExternalServiceError(
                "Calendar event end time must be after start time."
            )

        if idempotency_key:
            existing_event = self._get_existing_event(
                idempotency_key
            )

            if existing_event:
                logger.info(
                    "Returning existing calendar event "
                    "for idempotency key %s",
                    idempotency_key,
                )
                return existing_event

        event_id = self._generate_event_id(
            title=title,
            start_time=start_time,
            session_id=session_id,
            property_id=property_id,
        )

        event = CalendarEvent(
            event_id=event_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            timezone=timezone,
            property_id=property_id,
            session_id=session_id,
        )

        self.events[event_id] = event

        if idempotency_key:
            self._save_idempotency(
                idempotency_key=idempotency_key,
                event_id=event_id,
            )

        logger.info(
            "Calendar event created: %s",
            event_id,
        )

        return event

    def get_event(
        self,
        event_id: str,
    ) -> CalendarEvent | None:
        return self.events.get(event_id)

    def list_events(self) -> list[CalendarEvent]:
        return list(self.events.values())

    def _get_existing_event(
        self,
        idempotency_key: str,
    ) -> CalendarEvent | None:

        if self.idempotency_repository:
            record = self.idempotency_repository.get(
                idempotency_key
            )

            if record and record.resource_id:
                return self.events.get(
                    record.resource_id
                )

        for event in self.events.values():
            generated_key = self._event_fingerprint(
                event
            )

            if generated_key == idempotency_key:
                return event

        return None

    def _save_idempotency(
        self,
        idempotency_key: str,
        event_id: str,
    ) -> None:

        if not self.idempotency_repository:
            return

        self.idempotency_repository.save(
            idempotency_key=idempotency_key,
            operation="calendar.create_event",
            resource_id=event_id,
        )

    @staticmethod
    def _generate_event_id(
        title: str,
        start_time: datetime,
        session_id: str | None,
        property_id: str | None,
    ) -> str:
        raw = "|".join(
            [
                title,
                start_time.isoformat(),
                session_id or "",
                property_id or "",
            ]
        )

        return "mock_" + hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()[:20]

    @staticmethod
    def _event_fingerprint(
        event: CalendarEvent,
    ) -> str:
        raw = "|".join(
            [
                event.title,
                event.start_time.isoformat(),
                event.session_id or "",
                event.property_id or "",
            ]
        )

        return "calendar_" + hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()[:20]


class GoogleCalendarClient(CalendarClient):
    """
    Google Calendar adapter.

    The implementation is intentionally isolated from the rest
    of the application so the POC can run using MockCalendarClient
    without Google credentials.
    """

    def __init__(
        self,
        credentials_path: str,
        token_path: str,
        db: Session | None = None,
    ):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.idempotency_repository = (
            IdempotencyRepository(db)
            if db is not None
            else None
        )

    def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        timezone: str,
        property_id: str | None = None,
        session_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> CalendarEvent:

        try:
            from google.auth.transport.requests import (
                Request,
            )
            from google.oauth2.credentials import (
                Credentials,
            )
            from google_auth_oauthlib.flow import (
                InstalledAppFlow,
            )
            from googleapiclient.discovery import (
                build,
            )
        except ImportError as exc:
            raise ExternalServiceError(
                "Google Calendar dependencies are not installed."
            ) from exc

        if end_time <= start_time:
            raise ExternalServiceError(
                "Calendar event end time must be after start time."
            )

        if (
            idempotency_key
            and self.idempotency_repository
        ):
            existing = self.idempotency_repository.get(
                idempotency_key
            )

            if existing and existing.resource_id:
                return CalendarEvent(
                    event_id=existing.resource_id,
                    title=title,
                    start_time=start_time,
                    end_time=end_time,
                    timezone=timezone,
                    property_id=property_id,
                    session_id=session_id,
                )

        scopes = [
            "https://www.googleapis.com/auth/calendar.events"
        ]

        credentials = None

        try:
            credentials = Credentials.from_authorized_user_file(
                self.token_path,
                scopes,
            )
        except Exception:
            credentials = None

        if credentials and credentials.expired:
            if credentials.refresh_token:
                credentials.refresh(Request())

        if not credentials or not credentials.valid:
            if not self.credentials_path:
                raise ExternalServiceError(
                    "Google Calendar credentials are not configured."
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path,
                scopes,
            )

            credentials = flow.run_local_server(
                port=0
            )

        try:
            service = build(
                "calendar",
                "v3",
                credentials=credentials,
            )

            body = {
                "summary": title,
                "start": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": timezone,
                },
                "end": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": timezone,
                },
            }

            if property_id:
                body["description"] = (
                    f"Property ID: {property_id}"
                )

            response = service.events().insert(
                calendarId="primary",
                body=body,
            ).execute()

            event_id = response["id"]

            if (
                idempotency_key
                and self.idempotency_repository
            ):
                self.idempotency_repository.save(
                    idempotency_key=idempotency_key,
                    operation="calendar.create_event",
                    resource_id=event_id,
                )

            return CalendarEvent(
                event_id=event_id,
                title=title,
                start_time=start_time,
                end_time=end_time,
                timezone=timezone,
                property_id=property_id,
                session_id=session_id,
            )

        except ExternalServiceError:
            raise

        except Exception as exc:
            logger.exception(
                "Google Calendar event creation failed."
            )

            raise ExternalServiceError(
                "Unable to create Google Calendar event."
            ) from exc