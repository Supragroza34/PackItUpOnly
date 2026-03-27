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
    def setUp(self):
        self.student = self._create_user("student1", "student1@example.com", "student")
        self.staff = self._create_user("staff1", "staff1@example.com", "staff")
        self.admin = self._create_user("admin1", "admin@example.com", "admin")
        self.ticket = self._create_ticket()
        self.meeting_request = self._create_meeting_request()

    def _create_user(self, username, email, role):
        return User.objects.create_user(
            username=username,
            email=email,
            password="pass",
            role=role,
        )

    def _create_ticket(self):
        return Ticket.objects.create(
            user=self.student,
            type_of_issue="Test Issue",
            assigned_to=self.staff,
        )

    def _create_meeting_request(self):
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
        return MeetingRequest.objects.create(
            student=self.student,
            staff=self.staff,
            meeting_datetime=meeting_time,
            description="Need help with a ticket",
            status=MeetingRequest.Status.PENDING,
        )

    def _first_notification_for(self, user):
        return Notification.objects.filter(user=user).first()

    def test_notify_admin_on_ticket_creates_notifications(self):
        notify_admin_on_ticket(self.ticket)
        notif = self._first_notification_for(self.admin)
        self.assertIsNotNone(notif)
        self.assertIn("submitted a new ticket", notif.message)

    def test_notify_staff_on_assignment_creates_notification(self):
        notify_staff_on_assignment(self.ticket, self.staff)
        notif = self._first_notification_for(self.staff)
        self.assertIsNotNone(notif)
        self.assertIn("assigned ticket", notif.message)

    def test_notify_user_on_reply_creates_notification(self):
        notify_user_on_reply(self.ticket, self.staff)
        notif = self._first_notification_for(self.student)
        self.assertIsNotNone(notif)
        self.assertIn("replied to your ticket", notif.message)

    def test_notify_on_ticket_update_closed(self):
        self.ticket.status = Ticket.Status.CLOSED
        notify_on_ticket_update(self.ticket, self.staff)
        notif_student = self._first_notification_for(self.student)
        self.assertIn("has been closed", notif_student.message)
        notif_staff = self._first_notification_for(self.staff)
        self.assertIsNone(notif_staff)
        notif_admin = self._first_notification_for(self.admin)
        self.assertIn("has been closed", notif_admin.message)

    def test_notify_on_ticket_update_closed_notifies_assigned_staff_when_admin_closes(self):
        self.ticket.status = Ticket.Status.CLOSED
        notify_on_ticket_update(self.ticket, self.admin)

        notif_staff = self._first_notification_for(self.staff)
        self.assertIsNotNone(notif_staff)
        self.assertIn("has been closed", notif_staff.message)

    def test_notify_staff_on_meeting_request_creates_notification(self):
        notify_staff_on_meeting_request(self.meeting_request)
        notif = self._first_notification_for(self.staff)
        self.assertIsNotNone(notif)
        self.assertIn("submitted a meeting request", notif.message)

    def test_notify_student_on_meeting_response_accepted(self):
        self.meeting_request.status = "accepted"
        notify_student_on_meeting_response(self.meeting_request, self.staff)
        notif = self._first_notification_for(self.student)
        self.assertIsNotNone(notif)
        self.assertIn("has been accepted", notif.message)

    def test_notify_student_on_meeting_response_denied(self):
        self.meeting_request.status = "denied"
        notify_student_on_meeting_response(self.meeting_request, self.staff)
        notif = self._first_notification_for(self.student)
        self.assertIsNotNone(notif)
        self.assertIn("has been denied", notif.message)

    def test_notify_staff_on_student_reply_creates_notification(self):
        notify_staff_on_student_reply(self.ticket, self.student)
        notif = self._first_notification_for(self.staff)
        self.assertIsNotNone(notif)
        self.assertIn("replied to ticket", notif.message)

    def test_notify_staff_on_student_reply_no_staff_assigned(self):
        self.ticket.assigned_to = None
        notify_staff_on_student_reply(self.ticket, self.student)
        notif_count = Notification.objects.count()
        self.assertEqual(notif_count, 0)