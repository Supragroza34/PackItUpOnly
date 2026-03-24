from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from KCLTicketingSystems.models import Ticket, Reply, User
from django.db import models


class StaffDashboardViewTests(TestCase):

    """Group staff dashboard view checks so the user workflow is guarded against regressions."""
    def setUp(self):
        # Create users with unique emails
        """Establish shared fixtures so tests stay focused on behavior rather than setup details."""
        self.student = User.objects.create_user(
            first_name='Test',
            last_name='User',
            username='testuser',
            email='testuser@example.com',
            password='password123',
            k_number='K123456',
        )
        self.student2 = User.objects.create_user(
            first_name='Other',
            last_name='Student',
            username='otherstudent',
            email='otherstudent@example.com',
            password='password123',
            k_number='K654321'
        )

        # Create staff members
        self.staff1 = User.objects.create_user(
            username='staff1',
            email='staff1@example.com',
            password='password123',
            k_number='S654321',
            role=User.Role.STAFF,
        )
        self.staff2 = User.objects.create_user(
            username='staff2',
            email='staff2@example.com',
            password='password123',
            k_number='S123456',
            role=User.Role.STAFF,
        )

        # Create tickets for self.student
        self.ticket1 = Ticket.objects.create(
            user=self.student,
            type_of_issue='Software',
            department='IT',
            additional_details='Issue details 1',
            status=Ticket.Status.PENDING,
            assigned_to=self.staff1
        )
        self.ticket2 = Ticket.objects.create(
            user=self.student,
            type_of_issue='Hardware',
            department='Maintenance',
            additional_details='Issue details 2',
            status=Ticket.Status.PENDING,
            assigned_to=self.staff1
        )
        # Create closed ticket for self.student
        self.ticket3 = Ticket.objects.create(
            user=self.student,
            type_of_issue='Software',
            department='IT',
            additional_details='Issue details 1',
            status=Ticket.Status.CLOSED,
            assigned_to=self.staff1
        )
        # Create non-overdue ticket for self.student
        self.ticket4 = Ticket.objects.create(
            user=self.student,
            type_of_issue='Software',
            department='IT',
            additional_details='Issue details 1',
            status=Ticket.Status.IN_PROGRESS,
            assigned_to=self.staff1,
        )                

        # Add replies to ticket1
        self.reply1 = Reply.objects.create(
            ticket=self.ticket1,
            user=self.staff1,
            body='Reply 1'
        )
        self.reply2 = Reply.objects.create(
            ticket=self.ticket1,
            user=self.staff1,
            body='Reply 2'
        )

        # Ticket for student 2 assigned to staff 2 (should not appear in self.staff2 dashboard)
        self.other_ticket = Ticket.objects.create(
            user=self.student2,
            type_of_issue='Network',
            department='IT',
            additional_details='Other user ticket',
            status='open',
            assigned_to=self.staff2
        )

        # Initialize APIClient
        self.client = APIClient()

    def test_dashboard_requires_authentication(self):
        # Unauthenticated request should be blocked
        """Guard dashboard requires authentication in the staff dashboard view flow so regressions surface early."""
        response = self.client.get('/api/staff/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_staff_returns_access_error(self):
        """Guard non staff returns access error in the staff dashboard view flow so regressions surface early."""
        self.client.force_authenticate(user=self.student)
        response = self.client.get('/api/staff/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # self.assertEqual(response.detail, 'Staff access required')

    def test_authenticated_staff_dashboard_returns_their_tickets(self):
        # Authenticate the client
        """Guard authenticated staff dashboard returns their tickets in the staff dashboard view flow so regressions surface early."""
        self.client.force_authenticate(user=self.staff1)
        response = self.client.get('/api/staff/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Check tickets
        self.assertEqual(len(data), 3)
        ticket_ids = [t['id'] for t in data]
        self.assertIn(self.ticket1.id, ticket_ids)
        self.assertIn(self.ticket2.id, ticket_ids)

    def test_staff_cannot_see_others_staff_tickets(self):
        """Guard staff cannot see others staff tickets in the staff dashboard view flow so regressions surface early."""
        self.client.force_authenticate(user=self.staff1)
        response = self.client.get('/api/staff/dashboard/')
        data = response.json()
        ticket_ids = [t['id'] for t in data]
        self.assertNotIn(self.other_ticket.id, ticket_ids)

    def test_closed_filter(self):
        """Guard closed filter in the staff dashboard view flow so regressions surface early."""
        self.client.force_authenticate(user=self.staff1)
        response = self.client.get('/api/staff/dashboard/?filtering=closed')
        data = response.json()
        ticket_ids = [t['id'] for t in data]
        ticket_id = self.ticket3.id
        self.assertIn(ticket_id, ticket_ids)

    def test_overdue_filter(self):
        """Guard overdue filter in the staff dashboard view flow so regressions surface early."""
        self.client.force_authenticate(user=self.staff1)
        response = self.client.get('/api/staff/dashboard/?filtering=overdue')
        data = response.json()
        ticket_ids = [t['id'] for t in data]
        ticket_id = self.ticket4.id
        self.assertNotIn(ticket_id, ticket_ids)

    def test_all_filter(self):
        """Guard all filter in the staff dashboard view flow so regressions surface early."""
        self.client.force_authenticate(user=self.staff1)
        response = self.client.get('/api/staff/dashboard/?filtering=all')
        data = response.json()
        ticket_ids = [t['id'] for t in data]
        ticket_id1 = self.ticket1.id
        ticket_id2 = self.ticket2.id
        ticket_id3 = self.ticket3.id
        ticket_id4 = self.ticket4.id
        self.assertIn(ticket_id1, ticket_ids)
        self.assertIn(ticket_id2, ticket_ids)
        self.assertIn(ticket_id3, ticket_ids)
        self.assertIn(ticket_id4, ticket_ids)

    def test_search_bar(self):
        """Guard search bar in the staff dashboard view flow so regressions surface early."""
        self.other_ticket2 = Ticket.objects.create(
            user=self.student2,
            type_of_issue='Network',
            department='IT',
            additional_details='Other user ticket',
            status='open',
            assigned_to=self.staff1
        )
        self.client.force_authenticate(user=self.staff1)
        response = self.client.get('/api/staff/dashboard/?filtering=closed&search=Test')
        data = response.json()
        ticket_ids = [t['id'] for t in data]
        self.assertIn(self.ticket3.id, ticket_ids)
        self.assertNotIn(self.ticket2.id, ticket_ids)
        self.assertNotIn(self.other_ticket2.id, ticket_ids)

        response_2 = self.client.get('/api/staff/dashboard/?filtering=all&search=Other')
        data2 = response_2.json()
        ticket_ids_2 = [t['id'] for t in data2]
        self.assertNotIn(self.ticket3.id, ticket_ids_2)
        self.assertNotIn(self.ticket2.id, ticket_ids_2)
        self.assertIn(self.other_ticket2.id, ticket_ids_2)

    def test_closed_by(self):
        """Guard closed by in the staff dashboard view flow so regressions surface early."""
        self.other_ticket2 = Ticket.objects.create(
            user=self.student2,
            type_of_issue='Network',
            department='IT',
            additional_details='Other user ticket',
            status='open',
            assigned_to=self.staff1,
            closed_by=self.student2
        )

        self.client.force_authenticate(user=self.staff1)
        response = self.client.get('/api/staff/dashboard/?filtering=all')
        data = response.json()
