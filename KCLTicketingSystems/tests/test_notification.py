from django.test import TestCase
from django.contrib.auth import get_user_model
from KCLTicketingSystems.models.notification import Notification
from KCLTicketingSystems.models.ticket import Ticket
from KCLTicketingSystems.models.meeting_request import MeetingRequest

User = get_user_model()

class NotificationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="password123",
            role="student"
        )
        self.ticket = Ticket.objects.create(
            user=self.user,
            department="Informatics",
            type_of_issue="Test Issue",
            additional_details="Test details"
        )
        self.meeting_request = MeetingRequest.objects.create(
            student=self.user,
            staff=self.user,
            meeting_datetime=None,
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
