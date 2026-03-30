"""Tests for Office Hours."""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from ..models.office_hours import OfficeHours
import datetime

User = get_user_model()


class OfficeHoursModelTests(TestCase):

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='password123',
            role='staff'
        )
        self.office_hours = OfficeHours.objects.create(
            staff=self.staff_user,
            day_of_week=OfficeHours.DayOfWeek.MONDAY,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(17, 0),
        )

    # --- __str__ ---

    def test_str_representation(self):
        """Covers __str__."""
        expected = f"{self.staff_user} - Monday 09:00:00-17:00:00"
        self.assertEqual(str(self.office_hours), expected)

    # --- DayOfWeek choices ---

    def test_all_day_of_week_choices(self):
        """Covers all DayOfWeek TextChoices values."""
        days = [
            OfficeHours.DayOfWeek.MONDAY,
            OfficeHours.DayOfWeek.TUESDAY,
            OfficeHours.DayOfWeek.WEDNESDAY,
            OfficeHours.DayOfWeek.THURSDAY,
            OfficeHours.DayOfWeek.FRIDAY,
            OfficeHours.DayOfWeek.SATURDAY,
            OfficeHours.DayOfWeek.SUNDAY,
        ]
        for i, day in enumerate(days):
            oh = OfficeHours.objects.create(
                staff=self.staff_user,
                day_of_week=day,
                start_time=datetime.time(8, 0),
                end_time=datetime.time(10, 0),
            )
            self.assertEqual(oh.day_of_week, day)

    # --- clean() ---

    def test_clean_raises_when_start_equals_end(self):
        """Covers the ValidationError branch when start_time == end_time."""
        oh = OfficeHours(
            staff=self.staff_user,
            day_of_week=OfficeHours.DayOfWeek.TUESDAY,
            start_time=datetime.time(10, 0),
            end_time=datetime.time(10, 0),
        )
        with self.assertRaises(ValidationError):
            oh.clean()

    def test_clean_raises_when_start_after_end(self):
        """Covers the ValidationError branch when start_time > end_time."""
        oh = OfficeHours(
            staff=self.staff_user,
            day_of_week=OfficeHours.DayOfWeek.WEDNESDAY,
            start_time=datetime.time(17, 0),
            end_time=datetime.time(9, 0),
        )
        with self.assertRaises(ValidationError):
            oh.clean()

    def test_clean_passes_when_start_before_end(self):
        """Covers clean() passing without error."""
        oh = OfficeHours(
            staff=self.staff_user,
            day_of_week=OfficeHours.DayOfWeek.THURSDAY,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(17, 0),
        )
        try:
            oh.clean()
        except ValidationError:
            self.fail("clean() raised ValidationError unexpectedly")

    # --- Meta ---

    def test_ordering(self):
        """Covers Meta ordering."""
        self.assertEqual(OfficeHours._meta.ordering, ['day_of_week', 'start_time'])

    def test_verbose_name_plural(self):
        """Covers Meta verbose_name_plural."""
        self.assertEqual(OfficeHours._meta.verbose_name_plural, 'Office Hours')

    def test_db_table(self):
        """Covers Meta db_table."""
        self.assertEqual(OfficeHours._meta.db_table, 'KCLTicketingSystems_office_hours')

    # --- Fields ---

    def test_created_at_and_updated_at_are_set(self):
        """Covers auto_now_add and auto_now fields."""
        self.assertIsNotNone(self.office_hours.created_at)
        self.assertIsNotNone(self.office_hours.updated_at)

    def test_cascade_delete_with_staff(self):
        """Covers on_delete=CASCADE — deleting staff removes office hours."""
        oh_id = self.office_hours.id
        self.staff_user.delete()
        self.assertFalse(OfficeHours.objects.filter(id=oh_id).exists())

    def test_office_hours_valid(self):
        oh = OfficeHours(
            staff=self.staff_user,
            day_of_week="Monday",
            start_time=datetime.time(9, 0),
            end_time=datetime.time(17, 0)
        )
        # Should not raise
        oh.full_clean()

    def test_office_hours_invalid_times(self):
        oh = OfficeHours(
            staff=self.staff_user,
            day_of_week="Monday",
            start_time=datetime.time(17, 0),
            end_time=datetime.time(9, 0)
        )
        with self.assertRaises(ValidationError) as ctx:
            oh.full_clean()
        self.assertIn("Start time must be before end time", str(ctx.exception))

    def test_office_hours_str(self):
        oh = OfficeHours(
            staff=self.staff_user,
            day_of_week="Monday",
            start_time=datetime.time(9, 0),
            end_time=datetime.time(17, 0)
        )
        expected = f"{self.staff_user} - Monday 09:00:00-17:00:00"
        self.assertEqual(str(oh), expected)
