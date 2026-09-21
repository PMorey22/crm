from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from poc20.config import get_settings
from poc20.domain.exceptions import AppointmentError
from poc20.domain.models import Appointment


class AppointmentService:
    """
    Validates and prepares property-visit appointments.

    Calendar persistence is handled by the calendar client.
    This service owns business rules such as timezone,
    future dates, and business hours.
    """

    BUSINESS_START = time(10, 0)
    BUSINESS_END = time(18, 0)

    def __init__(
        self,
        timezone_name: str | None = None,
    ):
        settings = get_settings()
        self.timezone_name = (
            timezone_name or settings.timezone
        )

        try:
            self.timezone = ZoneInfo(
                self.timezone_name
            )
        except ZoneInfoNotFoundError as exc:
            raise AppointmentError(
                f"Invalid timezone: {self.timezone_name}"
            ) from exc

    def validate(
        self,
        appointment_date: date,
        appointment_time: time,
        property_id: str | None = None,
    ) -> Appointment:
        if appointment_date is None:
            raise AppointmentError(
                "Appointment date is required."
            )

        if appointment_time is None:
            raise AppointmentError(
                "Appointment time is required."
            )

        local_now = datetime.now(
            self.timezone
        )

        requested_datetime = datetime.combine(
            appointment_date,
            appointment_time,
        ).replace(
            tzinfo=self.timezone
        )

        if requested_datetime <= local_now:
            raise AppointmentError(
                "Appointment must be scheduled in the future."
            )

        if appointment_time < self.BUSINESS_START:
            raise AppointmentError(
                "Appointments cannot start before 10:00."
            )

        if appointment_time >= self.BUSINESS_END:
            raise AppointmentError(
                "Appointments must start before 18:00."
            )

        if requested_datetime.weekday() >= 6:
            raise AppointmentError(
                "Appointments are available Monday to Friday."
            )

        return Appointment(
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            timezone=self.timezone_name,
            confirmed=False,
            property_id=property_id,
        )

    def parse_datetime(
        self,
        value: str,
    ) -> datetime:
        if not value or not value.strip():
            raise AppointmentError(
                "Appointment datetime cannot be empty."
            )

        normalized = value.strip()

        try:
            parsed = datetime.fromisoformat(
                normalized
            )
        except ValueError as exc:
            raise AppointmentError(
                "Invalid appointment datetime format."
            ) from exc

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=self.timezone
            )
        else:
            parsed = parsed.astimezone(
                self.timezone
            )

        return parsed

    def create_from_datetime(
        self,
        value: str,
        property_id: str | None = None,
    ) -> Appointment:
        requested_datetime = self.parse_datetime(
            value
        )

        return self.validate(
            appointment_date=requested_datetime.date(),
            appointment_time=requested_datetime.time().replace(
                second=0,
                microsecond=0,
            ),
            property_id=property_id,
        )

    def next_business_day(
        self,
        from_date: date | None = None,
    ) -> date:
        current_date = (
            from_date
            or datetime.now(
                self.timezone
            ).date()
        )

        next_date = current_date + timedelta(
            days=1
        )

        while next_date.weekday() >= 5:
            next_date += timedelta(
                days=1
            )

        return next_date