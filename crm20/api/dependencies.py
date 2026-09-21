from sqlalchemy.orm import Session

from poc20.infrastructure.calendar_client import (
    CalendarClient,
    MockCalendarClient,
)
from poc20.infrastructure.property_repository import (
    PropertyRepository,
)
from poc20.infrastructure.task_client import (
    MockTaskClient,
    TaskClient,
)


def get_property_repository() -> PropertyRepository:
    return PropertyRepository()


def get_calendar_client(
    db: Session,
) -> CalendarClient:
    return MockCalendarClient(db)


def get_task_client(
    db: Session,
) -> TaskClient:
    return MockTaskClient(db)