from datetime import datetime
from zoneinfo import ZoneInfo

from poc20.infrastructure.calendar_client import (
    MockCalendarClient,
)


def test_calendar_idempotency() -> None:
    client = MockCalendarClient()

    start = datetime(
        2099,
        1,
        5,
        11,
        0,
        tzinfo=ZoneInfo("Asia/Kolkata"),
    )

    end = datetime(
        2099,
        1,
        5,
        12,
        0,
        tzinfo=ZoneInfo("Asia/Kolkata"),
    )

    first = client.create_event(
        title="Property Visit",
        start_time=start,
        end_time=end,
        timezone="Asia/Kolkata",
        session_id="session-1",
        property_id="P1",
        idempotency_key="visit-session-1-P1",
    )

    second = client.create_event(
        title="Property Visit",
        start_time=start,
        end_time=end,
        timezone="Asia/Kolkata",
        session_id="session-1",
        property_id="P1",
        idempotency_key="visit-session-1-P1",
    )

    assert first.event_id == second.event_id
    assert len(client.list_events()) == 1