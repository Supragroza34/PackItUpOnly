"""Tests for Notification."""

from django.test import TestCase
from django.contrib.auth import get_user_model
from KCLTicketingSystems.models.notification import Notification
from KCLTicketingSystems.models import Ticket, OfficeHours, MeetingRequest
import datetime
from django.utils import timezone

User = get_user_model()

class NotificationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="password123",
            role="student"
        )
        self.staff_user = User.objects.create_user(
            username="staff1",
            email="staff1@example.com",
            password="password123",
            role="staff"
        )
        self.ticket = Ticket.objects.create(
            user=self.user,
            department="Informatics",
            type_of_issue="Test Issue",
            additional_details="Test details"
        )
        from django.utils import timezone
        from datetime import timedelta
        from KCLTicketingSystems.models.office_hours import OfficeHours
        import datetime
        future_time = timezone.now() + timedelta(days=7)
        future_time = future_time.replace(hour=10, minute=0, second=0, microsecond=0)
        day_name = future_time.strftime("%A")
        OfficeHours.objects.create(
            staff=self.staff_user,
            day_of_week=day_name,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(17, 0),
        )
        self.meeting_request = MeetingRequest.objects.create(
            student=self.user,
            staff=self.staff_user,
            meeting_datetime=future_time,
            description="Test meeting"
        )

    def test_notification_str_with_ticket(self):
        notif = Notification.objects.create(
            user=self.user,
            title="Test Title",
            message="Test Message",
            ticket=self.ticket
        )
        expected = f"{self.user.username} - Test Title"
        self.assertEqual(str(notif), expected)

    def test_notification_str_with_meeting_request(self):
        notif = Notification.objects.create(
            user=self.user,
            title="Meeting Title",
            message="Meeting Message",
            meeting_request=self.meeting_request
        )
        expected = f"{self.user.username} - Meeting Title"
        self.assertEqual(str(notif), expected)

    def test_notification_str_with_no_ticket_or_meeting(self):
        notif = Notification.objects.create(
            user=self.user,
            title="No Link",
            message="No Link Message"
        )
        expected = f"{self.user.username} - No Link"
        self.assertEqual(str(notif), expected)
