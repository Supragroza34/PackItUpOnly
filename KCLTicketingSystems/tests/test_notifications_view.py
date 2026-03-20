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
        # Create test users
        self.student = User.objects.create_user(
            username="student1",
            email="student1@example.com",
            password="password123",
            role="student"
        )
        self.other_user = User.objects.create_user(
            username="student2",
            email="student2@example.com",
            password="password123",
            role="student"
        )

        # Create a ticket for the student
        self.ticket = Ticket.objects.create(
            user=self.student,
            type_of_issue="Test Issue",
            status=Ticket.Status.PENDING  
        )

        # Create notifications for testing
        self.notification1 = Notification.objects.create(
            user=self.student,
            title="Test Notification 1",
            message="Message 1",
            ticket=self.ticket
        )
        self.notification2 = Notification.objects.create(
            user=self.student,
            title="Test Notification 2",
            message="Message 2",
            ticket=self.ticket
        )

        # DRF API client
        self.client = APIClient()

    def test_list_notifications_authenticated_user(self):
        self.client.force_authenticate(user=self.student)
        url = reverse("notifications_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # 2 notifications

    def test_list_notifications_unauthenticated_user(self):
        url = reverse("notifications_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_mark_notification_read(self):
        self.client.force_authenticate(user=self.student)
        url = reverse("mark_notification_read", kwargs={"pk": self.notification1.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification1.refresh_from_db()
        self.assertTrue(self.notification1.is_read)

    def test_mark_notification_read_nonexistent(self):
        self.client.force_authenticate(user=self.student)
        url = reverse("mark_notification_read", kwargs={"pk": 9999})  # Non-existent
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_mark_notification_read_wrong_user(self):
        self.client.force_authenticate(user=self.other_user)
        url = reverse("mark_notification_read", kwargs={"pk": self.notification1.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  # cannot access other user's notifications