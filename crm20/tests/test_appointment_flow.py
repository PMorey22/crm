from datetime import date, time

import pytest

from poc20.domain.exceptions import AppointmentError
from poc20.services.appointment_service import (
    AppointmentService,
)


def test_valid_appointment() -> None:
    service = AppointmentService(
        timezone_name="Asia/Kolkata"
    )

    appointment = service.validate(
        appointment_date=date(2099, 1, 5),
        appointment_time=time(11, 0),
        property_id="P1",
    )

    assert appointment.appointment_date == date(
        2099,
        1,
        5,
    )

    assert appointment.appointment_time == time(
        11,
        0,
    )

    assert appointment.property_id == "P1"
    assert appointment.confirmed is False


def test_appointment_before_business_hours() -> None:
    service = AppointmentService(
        timezone_name="Asia/Kolkata"
    )

    with pytest.raises(AppointmentError):
        service.validate(
            appointment_date=date(2099, 1, 5),
            appointment_time=time(9, 0),
        )