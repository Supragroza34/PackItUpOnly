# KCLTicketingSystems/tests/test_notifications_view.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from KCLTicketingSystems.models import Notification, Ticket

User = get_user_model()


class NotificationViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self._create_users()
        self.ticket = self._create_ticket_for_student()
        self.notification1 = self._create_notification("Test Notification 1", "Message 1")
        self.notification2 = self._create_notification("Test Notification 2", "Message 2")

    def _create_users(self):
        self.student = User.objects.create_user(
            username="student1",
            email="student1@example.com",
            password="password123",
            role="student",
        )
        self.other_user = User.objects.create_user(
            username="student2",
            email="student2@example.com",
            password="password123",
            role="student",
        )

    def _create_ticket_for_student(self):
        return Ticket.objects.create(
            user=self.student,
            type_of_issue="Test Issue",
            status=Ticket.Status.PENDING,
        )

    def _create_notification(self, title, message):
        return Notification.objects.create(
            user=self.student,
            title=title,
            message=message,
            ticket=self.ticket
        )

    def _notifications_list_url(self):
        return reverse("notifications_list")

    def _mark_read_url(self, notification_id):
        return reverse("mark_notification_read", kwargs={"pk": notification_id})

    def test_list_notifications_authenticated_user(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self._notifications_list_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_notifications_unauthenticated_user(self):
        response = self.client.get(self._notifications_list_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_mark_notification_read(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.post(self._mark_read_url(self.notification1.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification1.refresh_from_db()
        self.assertTrue(self.notification1.is_read)

    def test_mark_notification_read_nonexistent(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.post(self._mark_read_url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_mark_notification_read_wrong_user(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(self._mark_read_url(self.notification1.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)