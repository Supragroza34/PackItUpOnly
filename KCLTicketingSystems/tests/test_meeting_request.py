from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from KCLTicketingSystems.models.meeting_request import MeetingRequest
from KCLTicketingSystems.models.office_hours import OfficeHours
from KCLTicketingSystems.models.user import User
import datetime

class MeetingRequestModelTest(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="student1",
            email="student1@example.com",
            password="password123",
            role=User.Role.STUDENT
        )
        self.staff = User.objects.create_user(
            username="staff1",
            email="staff1@example.com",
            password="password123",
            role=User.Role.STAFF
        )
        self.day_name = "Monday"
        self.office_hours = OfficeHours.objects.create(
            staff=self.staff,
            day_of_week=self.day_name,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(17, 0)
        )

    def test_meeting_request_within_office_hours(self):
        meeting_time = timezone.now() + datetime.timedelta(days=(7 - timezone.now().weekday()))
        meeting_time = meeting_time.replace(hour=10, minute=0, second=0, microsecond=0)
        mr = MeetingRequest(
            student=self.student,
            staff=self.staff,
            meeting_datetime=meeting_time,
            description="Test meeting"
        )
        # Should not raise
        mr.full_clean()

    def test_meeting_request_outside_office_hours(self):
        meeting_time = timezone.now() + datetime.timedelta(days=(7 - timezone.now().weekday()))
        meeting_time = meeting_time.replace(hour=20, minute=0, second=0, microsecond=0)
        mr = MeetingRequest(
            student=self.student,
            staff=self.staff,
            meeting_datetime=meeting_time,
            description="Test meeting"
        )
        with self.assertRaises(ValidationError) as ctx:
            mr.full_clean()
        self.assertIn("office hours", str(ctx.exception))

    def test_meeting_request_in_past(self):
        meeting_time = timezone.now() - datetime.timedelta(days=1)
        mr = MeetingRequest(
            student=self.student,
            staff=self.staff,
            meeting_datetime=meeting_time,
            description="Test meeting"
        )
        with self.assertRaises(ValidationError) as ctx:
            mr.full_clean()
        self.assertIn("in the past", str(ctx.exception))

    def test_meeting_request_clean_no_datetime(self):
        mr = MeetingRequest(
            student=self.student,
            staff=self.staff,
            meeting_datetime=None,
            description="Test meeting"
        )
        # Should not raise
        mr.clean()

    def test_meeting_request_str(self):
        meeting_time = timezone.now() + datetime.timedelta(days=1)
        mr = MeetingRequest(
            student=self.student,
            staff=self.staff,
            meeting_datetime=meeting_time,
            description="Test meeting"
        )
        expected = f"{self.student} -> {self.staff} on {meeting_time}"
        self.assertEqual(str(mr), expected)
