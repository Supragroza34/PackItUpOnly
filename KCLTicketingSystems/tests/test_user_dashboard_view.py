from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from ..models import Ticket, Reply

User = get_user_model()


class UserDashboardViewTests(TestCase):
    DASHBOARD_URL = "/api/dashboard/"

    def setUp(self):
        self.client = APIClient()
        self._create_users()
        self._create_user_tickets_and_replies()
        self._create_other_user_ticket()

    def _create_users(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="password123",
            k_number="K123456",
        )
        self.other_user = User.objects.create_user(
            username="otheruser",
            email="otheruser@example.com",
            password="password123",
            k_number="K654321",
        )

    def _create_ticket(self, user, issue, department, details, status):
        return Ticket.objects.create(
            user=user,
            type_of_issue=issue,
            department=department,
            additional_details=details,
            status=status,
        )

    def _create_user_tickets_and_replies(self):
        self.ticket1 = self._create_ticket(
            self.user,
            "Software",
            "IT",
            "Issue details 1",
            "open",
        )
        self.ticket2 = self._create_ticket(
            self.user,
            "Hardware",
            "Maintenance",
            "Issue details 2",
            "closed",
        )
        self.reply1 = Reply.objects.create(ticket=self.ticket1, user=self.user, body="Reply 1")
        self.reply2 = Reply.objects.create(ticket=self.ticket1, user=self.user, body="Reply 2")

    def _create_other_user_ticket(self):
        self.other_ticket = self._create_ticket(
            self.other_user,
            "Network",
            "IT",
            "Other user ticket",
            "open",
        )

    def _auth(self):
        self.client.force_authenticate(user=self.user)

    def _dashboard_response(self):
        return self.client.get(self.DASHBOARD_URL)

    def test_dashboard_requires_authentication(self):
        response = self._dashboard_response()
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_authenticated_user_dashboard_returns_correct_data(self):
        self._auth()
        response = self._dashboard_response()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertEqual(data['user']['id'], self.user.id)
        self.assertEqual(data['user']['k_number'], self.user.k_number)

        self.assertEqual(len(data['tickets']), 2)
        ticket_ids = [t['id'] for t in data['tickets']]
        self.assertIn(self.ticket1.id, ticket_ids)
        self.assertIn(self.ticket2.id, ticket_ids)

        ticket1_data = next(t for t in data['tickets'] if t['id'] == self.ticket1.id)
        self.assertEqual(len(ticket1_data['replies']), 2)
        reply_bodies = [r['body'] for r in ticket1_data['replies']]
        self.assertIn('Reply 1', reply_bodies)
        self.assertIn('Reply 2', reply_bodies)

    def test_user_cannot_see_others_tickets(self):
        self._auth()
        response = self._dashboard_response()
        data = response.json()
        ticket_ids = [t['id'] for t in data['tickets']]
        self.assertNotIn(self.other_ticket.id, ticket_ids)

    def test_closed_ticket_has_closed_by_role(self):
        self.ticket2.closed_by = self.user
        self.ticket2.save()

        self._auth()
        response = self._dashboard_response()
        data = response.json().get('tickets', [])

        ticket2_data = next(t for t in data if t['id'] == self.ticket2.id)

        self.assertEqual(ticket2_data["closed_by_role"], "student")

    def test_ticket_with_no_replies(self):
        self._auth()
        response = self._dashboard_response()
        data = response.json()

        ticket2_data = next(t for t in data['tickets'] if t['id'] == self.ticket2.id)

        self.assertEqual(ticket2_data["replies"], [])

