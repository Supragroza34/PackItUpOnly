"""Tests for Student Meeting Request."""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import datetime

from ..models.meeting_request import MeetingRequest
from ..models.office_hours import OfficeHours

User = get_user_model()


class MeetingRequestModelTests(TestCase):

    def setUp(self):
        self.student = User.objects.create_user(
            username='student_mr',
            email='student_mr@test.com',
            password='testpass123',
            role=User.Role.STUDENT,
            department='Informatics',
            k_number='90001001',
        )
        self.staff = User.objects.create_user(
            username='staff_mr',
            email='staff_mr@test.com',
            password='testpass123',
            role=User.Role.STAFF,
            department='Informatics',
            k_number='90001002',
        )

        self.future_monday = self._next_weekday(0, hour=10) 

        OfficeHours.objects.create(
            staff=self.staff,
            day_of_week='Monday',
            start_time=datetime.time(9, 0),
            end_time=datetime.time(17, 0),
        )

    def _next_weekday(self, weekday, hour=10):
        """Return next occurrence of given weekday (0=Mon ... 6=Sun) in the future."""
        now = timezone.now()
        days_ahead = weekday - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        target = now + timedelta(days=days_ahead)
        return target.replace(hour=hour, minute=0, second=0, microsecond=0)

    def test_str_representation(self):
        mr = MeetingRequest(
            student=self.student,
            staff=self.staff,
            meeting_datetime=self.future_monday,
            description='Discussion',
            status=MeetingRequest.Status.PENDING,
        )
        expected = f"{self.student} -> {self.staff} on {self.future_monday}"
        self.assertEqual(str(mr), expected)

    def test_status_choices(self):
        self.assertEqual(MeetingRequest.Status.PENDING, 'pending')
        self.assertEqual(MeetingRequest.Status.ACCEPTED, 'accepted')
        self.assertEqual(MeetingRequest.Status.DENIED, 'denied')

    def test_clean_returns_early_when_no_meeting_datetime(self):
        """Covers the `if not self.meeting_datetime: return` branch."""
        mr = MeetingRequest(
            student=self.student,
            staff=self.staff,
            meeting_datetime=None,
            description='No date yet',
        )
        try:
            mr.clean()
        except ValidationError:
            self.fail("clean() raised ValidationError when meeting_datetime is None")

    def test_clean_raises_when_outside_office_hours(self):
        """Covers the ValidationError when no matching office hours block exists."""
        # Saturday — no office hours created for Saturday
        future_saturday = self._next_weekday(5, hour=10)
        mr = MeetingRequest(
            student=self.student,
            staff=self.staff,
            meeting_datetime=future_saturday,
            description='Weekend meeting',
        )
        with self.assertRaises(ValidationError) as ctx:
            mr.clean()
        self.assertIn("office hours", str(ctx.exception))

    def test_clean_raises_when_time_before_office_hours(self):
        """Meeting time exists on correct day but before start_time."""
        future_monday_early = self._next_weekday(0, hour=7) 
        mr = MeetingRequest(
            student=self.student,
            staff=self.staff,
            meeting_datetime=future_monday_early,
            description='Too early',
        )
        with self.assertRaises(ValidationError):
            mr.clean()

    def test_clean_raises_when_time_after_office_hours(self):
        """Meeting time exists on correct day but after end_time."""
        future_monday_late = self._next_weekday(0, hour=18)  
        mr = MeetingRequest(
            student=self.student,
            staff=self.staff,
            meeting_datetime=future_monday_late,
            description='Too late',
        )
        with self.assertRaises(ValidationError):
            mr.clean()

    def test_clean_raises_when_meeting_in_the_past(self):
        """Covers the `meeting_datetime < timezone.now()` branch."""
        past_monday = timezone.now() - timedelta(days=7)
        past_monday = past_monday.replace(hour=10, minute=0, second=0, microsecond=0)
        mr = MeetingRequest(
            student=self.student,
            staff=self.staff,
            meeting_datetime=past_monday,
            description='Past meeting',
        )
        with self.assertRaises(ValidationError) as ctx:
            mr.clean()
        self.assertIn("past", str(ctx.exception))

    def test_clean_passes_for_valid_future_meeting_within_office_hours(self):
        """Covers the happy path — no ValidationError raised."""
        mr = MeetingRequest(
            student=self.student,
            staff=self.staff,
            meeting_datetime=self.future_monday,
            description='Valid meeting',
        )
        try:
            mr.clean()
        except ValidationError:
            self.fail("clean() raised ValidationError for a valid meeting")

    def test_save_calls_full_clean(self):
        """Covers save() calling full_clean() before super().save()."""
        mr = MeetingRequest(
            student=self.student,
            staff=self.staff,
            meeting_datetime=self.future_monday,
            description='Save test',
        )
        mr.save()
        self.assertIsNotNone(mr.pk)

    def test_save_raises_when_invalid(self):
        """Covers save() propagating ValidationError from full_clean()."""
        future_saturday = self._next_weekday(5, hour=10)
        mr = MeetingRequest(
            student=self.student,
            staff=self.staff,
            meeting_datetime=future_saturday,
            description='Invalid save',
        )
        with self.assertRaises(ValidationError):
            mr.save()

    def test_ordering(self):
        self.assertEqual(MeetingRequest._meta.ordering, ['-created_at'])

    def test_db_table(self):
        self.assertEqual(MeetingRequest._meta.db_table, 'KCLTicketingSystems_meeting_request')

    def test_created_at_and_updated_at_set_on_save(self):
        mr = MeetingRequest(
            student=self.student,
            staff=self.staff,
            meeting_datetime=self.future_monday,
            description='Timestamps test',
        )
        mr.save()
        self.assertIsNotNone(mr.created_at)
        self.assertIsNotNone(mr.updated_at)

    def test_cascade_delete_on_student(self):
        mr = MeetingRequest.objects.create(
            student=self.student,
            staff=self.staff,
            meeting_datetime=self.future_monday,
            description='Cascade student',
        )
        mr_id = mr.id
        self.student.delete()
        self.assertFalse(MeetingRequest.objects.filter(id=mr_id).exists())

    def test_cascade_delete_on_staff(self):
        mr = MeetingRequest.objects.create(
            student=self.student,
            staff=self.staff,
            meeting_datetime=self.future_monday,
            description='Cascade staff',
        )
        mr_id = mr.id
        self.staff.delete()
        self.assertFalse(MeetingRequest.objects.filter(id=mr_id).exists())