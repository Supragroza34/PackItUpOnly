from django.test import TestCase
from django.core.exceptions import ValidationError
from KCLTicketingSystems.models.office_hours import OfficeHours
from KCLTicketingSystems.models.user import User
import datetime

class OfficeHoursModelTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="staff1",
            email="staff1@example.com",
            password="password123",
            role=User.Role.STAFF
        )

    def test_office_hours_valid(self):
        oh = OfficeHours(
            staff=self.staff,
            day_of_week="Monday",
            start_time=datetime.time(9, 0),
            end_time=datetime.time(17, 0)
        )
        # Should not raise
        oh.full_clean()

    def test_office_hours_invalid_times(self):
        oh = OfficeHours(
            staff=self.staff,
            day_of_week="Monday",
            start_time=datetime.time(17, 0),
            end_time=datetime.time(9, 0)
        )
        with self.assertRaises(ValidationError) as ctx:
            oh.full_clean()
        self.assertIn("Start time must be before end time", str(ctx.exception))

    def test_office_hours_str(self):
        oh = OfficeHours(
            staff=self.staff,
            day_of_week="Monday",
            start_time=datetime.time(9, 0),
            end_time=datetime.time(17, 0)
        )
        expected = f"{self.staff} - Monday 09:00:00-17:00:00"
        self.assertEqual(str(oh), expected)
