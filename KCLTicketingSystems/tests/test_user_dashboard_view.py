from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from ..models import Ticket, Reply

User = get_user_model()

class UserDashboardViewTests(TestCase):

    """Group user dashboard view checks so the user workflow is guarded against regressions."""
    def setUp(self):
        # Create users with unique emails
        """Establish shared fixtures so tests stay focused on behavior rather than setup details."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123',
            k_number='K123456'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='otheruser@example.com',
            password='password123',
            k_number='K654321'
        )

        # Create tickets for self.user
        self.ticket1 = Ticket.objects.create(
            user=self.user,
            type_of_issue='Software',
            department='IT',
            additional_details='Issue details 1',
            status='open'
        )
        self.ticket2 = Ticket.objects.create(
            user=self.user,
            type_of_issue='Hardware',
            department='Maintenance',
            additional_details='Issue details 2',
            status='closed'
        )

        # Add replies to ticket1
        self.reply1 = Reply.objects.create(
            ticket=self.ticket1,
            user=self.user,
            body='Reply 1'
        )
        self.reply2 = Reply.objects.create(
            ticket=self.ticket1,
            user=self.user,
            body='Reply 2'
        )

        # Ticket for other user (should not appear in self.user dashboard)
        self.other_ticket = Ticket.objects.create(
            user=self.other_user,
            type_of_issue='Network',
            department='IT',
            additional_details='Other user ticket',
            status='open'
        )

        # Initialize APIClient
        self.client = APIClient()

    def test_dashboard_requires_authentication(self):
        # Unauthenticated request should be blocked
        """Guard dashboard requires authentication in the user dashboard view flow so regressions surface early."""
        response = self.client.get('/api/dashboard/')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_authenticated_user_dashboard_returns_correct_data(self):
        # Authenticate the client
        """Guard authenticated user dashboard returns correct data in the user dashboard view flow so regressions surface early."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        # Check user data
        self.assertEqual(data['user']['id'], self.user.id)
        self.assertEqual(data['user']['k_number'], self.user.k_number)

        # Check tickets
        self.assertEqual(len(data['tickets']), 2)
        ticket_ids = [t['id'] for t in data['tickets']]
        self.assertIn(self.ticket1.id, ticket_ids)
        self.assertIn(self.ticket2.id, ticket_ids)

        # Check replies for ticket1
        ticket1_data = next(t for t in data['tickets'] if t['id'] == self.ticket1.id)
        self.assertEqual(len(ticket1_data['replies']), 2)
        reply_bodies = [r['body'] for r in ticket1_data['replies']]
        self.assertIn('Reply 1', reply_bodies)
        self.assertIn('Reply 2', reply_bodies)

    def test_user_cannot_see_others_tickets(self):
        """Guard user cannot see others tickets in the user dashboard view flow so regressions surface early."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/dashboard/')
        data = response.json()
        ticket_ids = [t['id'] for t in data['tickets']]
        self.assertNotIn(self.other_ticket.id, ticket_ids)

    def test_closed_ticket_has_closed_by_role(self):
        # Set closed_by for ticket2
        """Guard closed ticket has closed by role in the user dashboard view flow so regressions surface early."""
        self.ticket2.closed_by = self.user
        self.ticket2.save()

        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/dashboard/')
        data = response.json().get('tickets', [])

        ticket2_data = next(t for t in data if t['id'] == self.ticket2.id)

        self.assertEqual(ticket2_data["closed_by_role"], "student")

    def test_ticket_with_no_replies(self):
        """Guard ticket with no replies in the user dashboard view flow so regressions surface early."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/dashboard/')
        data = response.json()

        ticket2_data = next(t for t in data['tickets'] if t['id'] == self.ticket2.id)

        self.assertEqual(ticket2_data["replies"], [])

