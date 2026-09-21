from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from poc20.config import get_settings
from poc20.domain.enums import LeadStage
from poc20.domain.models import LeadSession


class FollowUp:
    def __init__(
        self,
        session_id: str,
        scheduled_at: datetime,
        reason: str,
        status: str = "PENDING",
    ):
        self.session_id = session_id
        self.scheduled_at = scheduled_at
        self.reason = reason
        self.status = status


class FollowUpService:
    """
    Determines when a lead should receive a follow-up.

    Scheduling is separated from delivery. The actual message/task
    delivery can be handled by n8n or another external worker.
    """

    def __init__(
        self,
        timezone_name: str | None = None,
    ):
        settings = get_settings()

        self.timezone_name = (
            timezone_name or settings.timezone
        )

        self.timezone = ZoneInfo(
            self.timezone_name
        )

    def create_follow_up(
        self,
        session: LeadSession,
        now: datetime | None = None,
    ) -> FollowUp | None:
        current_time = now or datetime.now(
            self.timezone
        )

        if current_time.tzinfo is None:
            current_time = current_time.replace(
                tzinfo=self.timezone
            )
        else:
            current_time = current_time.astimezone(
                self.timezone
            )

        if session.stage == LeadStage.COMPLETED:
            return None

        if session.stage == LeadStage.APPOINTMENT_CONFIRMATION:
            return FollowUp(
                session_id=session.session_id,
                scheduled_at=current_time + timedelta(
                    hours=2
                ),
                reason="Confirm scheduled property visit",
            )

        if session.stage == LeadStage.MATCHED:
            return FollowUp(
                session_id=session.session_id,
                scheduled_at=current_time + timedelta(
                    hours=24
                ),
                reason="Follow up on property recommendations",
            )

        if session.stage == LeadStage.QUALIFIED:
            return FollowUp(
                session_id=session.session_id,
                scheduled_at=current_time + timedelta(
                    hours=24
                ),
                reason="Follow up with qualified lead",
            )

        if session.stage == LeadStage.QUALIFYING:
            return FollowUp(
                session_id=session.session_id,
                scheduled_at=current_time + timedelta(
                    hours=48
                ),
                reason="Collect missing lead requirements",
            )

        return None

    def should_follow_up(
        self,
        follow_up: FollowUp,
        now: datetime | None = None,
    ) -> bool:
        if follow_up.status != "PENDING":
            return False

        current_time = now or datetime.now(
            self.timezone
        )

        if current_time.tzinfo is None:
            current_time = current_time.replace(
                tzinfo=self.timezone
            )
        else:
            current_time = current_time.astimezone(
                self.timezone
            )

        scheduled_at = follow_up.scheduled_at

        if scheduled_at.tzinfo is None:
            scheduled_at = scheduled_at.replace(
                tzinfo=self.timezone
            )
        else:
            scheduled_at = scheduled_at.astimezone(
                self.timezone
            )

        return current_time >= scheduled_at

    @staticmethod
    def mark_completed(
        follow_up: FollowUp,
    ) -> FollowUp:
        follow_up.status = "COMPLETED"
        return follow_up

    @staticmethod
    def mark_cancelled(
        follow_up: FollowUp,
    ) -> FollowUp:
        follow_up.status = "CANCELLED"
        return follow_up