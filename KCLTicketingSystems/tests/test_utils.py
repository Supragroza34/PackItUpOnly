from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from ..models import Ticket, Notification, MeetingRequest, OfficeHours
from ..utils import (
    notify_admin_on_ticket,
    notify_staff_on_assignment,
    notify_user_on_reply,
    notify_on_ticket_update,
    notify_staff_on_meeting_request,
    notify_student_on_meeting_response,
    notify_staff_on_student_reply
)

User = get_user_model()

class NotificationUtilsTests(TestCase):
    """Group utils checks so the user workflow is guarded against regressions."""
    def setUp(self):
        # Users
        """Establish shared fixtures so tests stay focused on behavior rather than setup details."""
        # We pre-seed distinct student, staff, and admin roles here to ensure 
        # cross-role notification logic can be tested in isolation without redundant database writes.
        self.student = User.objects.create_user(
            username="student1", email="student1@example.com", password="pass", role="student"
        )
        self.staff = User.objects.create_user(
            username="staff1", email="staff1@example.com", password="pass", role="staff"
        )
        self.admin = User.objects.create_user(
            username="admin1", email="admin@example.com", password="pass", role="admin"
        )

        # Ticket
        self.ticket = Ticket.objects.create(
            user=self.student,
            type_of_issue="Test Issue",
            assigned_to=self.staff
        )

        # Valid office hours + meeting request fixture for notification tests
        # We explicitly calculate a future date for the meeting to prevent the model's 
        # timezone validation layer from rejecting the fixture as a "past event".
        meeting_time = (timezone.now() + timezone.timedelta(days=1)).replace(
            hour=10,
            minute=0,
            second=0,
            microsecond=0,
        )
        OfficeHours.objects.create(
            staff=self.staff,
            day_of_week=meeting_time.strftime("%A"),
            start_time=meeting_time.replace(hour=9).time(),
            end_time=meeting_time.replace(hour=17).time(),
        )
        self.meeting_request = MeetingRequest.objects.create(
            student=self.student,
            staff=self.staff,
            meeting_datetime=meeting_time,
            description="Need help with a ticket",
            status=MeetingRequest.Status.PENDING,
        )

    def test_notify_admin_on_ticket_creates_notifications(self):
        """Guard notify admin on ticket creates notifications in the utils flow so regressions surface early."""
        notify_admin_on_ticket(self.ticket)
        notif = Notification.objects.filter(user=self.admin).first()
        self.assertIsNotNone(notif)
        self.assertIn("submitted a new ticket", notif.message)

    def test_notify_staff_on_assignment_creates_notification(self):
        """Guard notify staff on assignment creates notification in the utils flow so regressions surface early."""
        notify_staff_on_assignment(self.ticket, self.staff)
        notif = Notification.objects.filter(user=self.staff).first()
        self.assertIsNotNone(notif)
        self.assertIn("assigned ticket", notif.message)

    def test_notify_user_on_reply_creates_notification(self):
        """Guard notify user on reply creates notification in the utils flow so regressions surface early."""
        notify_user_on_reply(self.ticket, self.staff)
        notif = Notification.objects.filter(user=self.student).first()
        self.assertIsNotNone(notif)
        self.assertIn("replied to your ticket", notif.message)

    def test_notify_on_ticket_update_closed(self):
        """Guard notify on ticket update closed in the utils flow so regressions surface early."""
        self.ticket.status = Ticket.Status.CLOSED
        notify_on_ticket_update(self.ticket, self.staff)
        # Student should be notified
        notif_student = Notification.objects.filter(user=self.student).first()
        self.assertIn("has been closed", notif_student.message)
        
        notif_staff = Notification.objects.filter(user=self.staff).first()
        self.assertIsNone(notif_staff)
        # Admin should be notified
        notif_admin = Notification.objects.filter(user=self.admin).first()
        self.assertIn("has been closed", notif_admin.message)

    def test_notify_on_ticket_update_closed_notifies_assigned_staff_when_admin_closes(self):
        """Guard notify on ticket update closed notifies assigned staff when admin closes in the utils flow so regressions surface early."""
        self.ticket.status = Ticket.Status.CLOSED
        notify_on_ticket_update(self.ticket, self.admin)

        notif_staff = Notification.objects.filter(user=self.staff).first()
        self.assertIsNotNone(notif_staff)
        self.assertIn("has been closed", notif_staff.message)

    def test_notify_staff_on_meeting_request_creates_notification(self):
        """Guard notify staff on meeting request creates notification in the utils flow so regressions surface early."""
        notify_staff_on_meeting_request(self.meeting_request)
        notif = Notification.objects.filter(user=self.staff).first()
        self.assertIsNotNone(notif)
        self.assertIn("submitted a meeting request", notif.message)

    def test_notify_student_on_meeting_response_accepted(self):
        """Guard notify student on meeting response accepted in the utils flow so regressions surface early."""
        self.meeting_request.status = "accepted"
        notify_student_on_meeting_response(self.meeting_request, self.staff)
        notif = Notification.objects.filter(user=self.student).first()
        self.assertIsNotNone(notif)
        self.assertIn("has been accepted", notif.message)

    def test_notify_student_on_meeting_response_denied(self):
        """Guard notify student on meeting response denied in the utils flow so regressions surface early."""
        self.meeting_request.status = "denied"
        notify_student_on_meeting_response(self.meeting_request, self.staff)
        notif = Notification.objects.filter(user=self.student).first()
        self.assertIsNotNone(notif)
        self.assertIn("has been denied", notif.message)

    def test_notify_staff_on_student_reply_creates_notification(self):
        """Guard notify staff on student reply creates notification in the utils flow so regressions surface early."""
        notify_staff_on_student_reply(self.ticket, self.student)
        notif = Notification.objects.filter(user=self.staff).first()
        self.assertIsNotNone(notif)
        self.assertIn("replied to ticket", notif.message)

    def test_notify_staff_on_student_reply_no_staff_assigned(self):
        """Guard notify staff on student reply no staff assigned in the utils flow so regressions surface early."""
        # Nullifying the assignment validates that the notification system fails gracefully 
        # and doesn't throw a NullPointerException when a ticket is in the open pool.
        self.ticket.assigned_to = None
        notify_staff_on_student_reply(self.ticket, self.student)
        notif_count = Notification.objects.count()
        self.assertEqual(notif_count, 0)