from datetime import datetime
from zoneinfo import ZoneInfo

from poc20.domain.enums import LeadStage
from poc20.domain.models import LeadSession
from poc20.services.followup_service import (
    FollowUpService,
)


def test_qualified_lead_followup() -> None:
    service = FollowUpService(
        timezone_name="Asia/Kolkata"
    )

    session = LeadSession(
        session_id="lead-1",
        stage=LeadStage.QUALIFIED,
    )

    now = datetime(
        2026,
        9,
        21,
        10,
        0,
        tzinfo=ZoneInfo("Asia/Kolkata"),
    )

    follow_up = service.create_follow_up(
        session=session,
        now=now,
    )

    assert follow_up is not None
    assert follow_up.session_id == "lead-1"
    assert follow_up.status == "PENDING"
    assert follow_up.reason == (
        "Follow up with qualified lead"
    )


def test_completed_lead_has_no_followup() -> None:
    service = FollowUpService(
        timezone_name="Asia/Kolkata"
    )

    session = LeadSession(
        session_id="lead-2",
        stage=LeadStage.COMPLETED,
    )

    follow_up = service.create_follow_up(
        session=session
    )

    assert follow_up is None