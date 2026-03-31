"""Business rules for meeting slot validation."""

from datetime import timedelta, datetime as dt_type

from ..models.meeting_request import MeetingRequest
from ..models.office_hours import OfficeHours


def validate_meeting_slot(staff, meeting_datetime):
    """
    Validate meeting policy constraints for a proposed slot.

    Raises:
        ValueError: if the slot violates interval, office-hour, or conflict rules.
    """
    _validate_quarter_hour_boundary(meeting_datetime)
    _validate_within_office_hours(staff=staff, meeting_datetime=meeting_datetime)
    _validate_no_conflict(staff=staff, meeting_datetime=meeting_datetime)


def _validate_quarter_hour_boundary(meeting_datetime):
    if meeting_datetime.minute % 15 != 0 or meeting_datetime.second != 0:
        raise ValueError(
            "Meetings must start at a 15-minute interval (e.g. 09:00, 09:15, 09:30, 09:45)."
        )


def _validate_within_office_hours(staff, meeting_datetime):
    day_name = meeting_datetime.strftime("%A")
    meeting_time = meeting_datetime.time()
    slot_end_time = (
        dt_type.combine(meeting_datetime.date(), meeting_time) + timedelta(minutes=15)
    ).time()
    in_office_hours = OfficeHours.objects.filter(
        staff=staff,
        day_of_week=day_name,
        start_time__lte=meeting_time,
        end_time__gte=slot_end_time,
    ).exists()
    if not in_office_hours:
        raise ValueError(
            "The selected time is not within the staff member's office hours. "
            "Please choose an available slot."
        )


def _validate_no_conflict(staff, meeting_datetime):
    conflict_exists = MeetingRequest.objects.filter(
        staff=staff,
        meeting_datetime=meeting_datetime,
        status__in=[MeetingRequest.Status.PENDING, MeetingRequest.Status.ACCEPTED],
    ).exists()
    if conflict_exists:
        raise ValueError("This time slot is already taken. Please choose another.")
