from django.test import TestCase
from django.contrib.auth import get_user_model
from ..models import Ticket, Notification
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
    def setUp(self):
        # Users
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

        # Meeting request mock
        class MeetingRequest:
            def __init__(self, student, staff, status="pending"):
                self.student = student
                self.staff = staff
                self.status = status
        self.meeting_request = MeetingRequest(self.student, self.staff)

    def test_notify_admin_on_ticket_creates_notifications(self):
        notify_admin_on_ticket(self.ticket)
        notif = Notification.objects.filter(user=self.admin).first()
        self.assertIsNotNone(notif)
        self.assertIn("submitted a new ticket", notif.message)

    def test_notify_staff_on_assignment_creates_notification(self):
        notify_staff_on_assignment(self.ticket, self.staff)
        notif = Notification.objects.filter(user=self.staff).first()
        self.assertIsNotNone(notif)
        self.assertIn("assigned ticket", notif.message)

    def test_notify_user_on_reply_creates_notification(self):
        notify_user_on_reply(self.ticket, self.staff)
        notif = Notification.objects.filter(user=self.student).first()
        self.assertIsNotNone(notif)
        self.assertIn("replied to your ticket", notif.message)

    def test_notify_on_ticket_update_closed(self):
        self.ticket.status = Ticket.Status.CLOSED
        notify_on_ticket_update(self.ticket, self.staff)
        # Student should be notified
        notif_student = Notification.objects.filter(user=self.student).first()
        self.assertIn("has been closed", notif_student.message)
        # Staff should be notified
        notif_staff = Notification.objects.filter(user=self.staff).first()
        self.assertIn("has been closed", notif_staff.message)
        # Admin should be notified
        notif_admin = Notification.objects.filter(user=self.admin).first()
        self.assertIn("has been closed", notif_admin.message)

    def test_notify_staff_on_meeting_request_creates_notification(self):
        notify_staff_on_meeting_request(self.meeting_request)
        notif = Notification.objects.filter(user=self.staff).first()
        self.assertIsNotNone(notif)
        self.assertIn("submitted a meeting request", notif.message)

    def test_notify_student_on_meeting_response_accepted(self):
        self.meeting_request.status = "accepted"
        notify_student_on_meeting_response(self.meeting_request, self.staff)
        notif = Notification.objects.filter(user=self.student).first()
        self.assertIsNotNone(notif)
        self.assertIn("has been accepted", notif.message)

    def test_notify_student_on_meeting_response_denied(self):
        self.meeting_request.status = "denied"
        notify_student_on_meeting_response(self.meeting_request, self.staff)
        notif = Notification.objects.filter(user=self.student).first()
        self.assertIsNotNone(notif)
        self.assertIn("has been denied", notif.message)

    def test_notify_staff_on_student_reply_creates_notification(self):
        notify_staff_on_student_reply(self.ticket, self.student)
        notif = Notification.objects.filter(user=self.staff).first()
        self.assertIsNotNone(notif)
        self.assertIn("replied to ticket", notif.message)

    def test_notify_staff_on_student_reply_no_staff_assigned(self):
        self.ticket.assigned_to = None
        notify_staff_on_student_reply(self.ticket, self.student)
        notif_count = Notification.objects.count()
        self.assertEqual(notif_count, 0)