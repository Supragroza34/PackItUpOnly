from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from KCLTicketingSystems.models import Ticket, Reply, User
from django.db import models
from django.utils import timezone
from datetime import timedelta, datetime


class StaffDashboardViewTests(TestCase):

    def setUp(self):
        # Create users with unique emails
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
        response = self.client.get('/api/staff/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_staff_returns_access_error(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get('/api/staff/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # self.assertEqual(response.detail, 'Staff access required')

    def test_authenticated_staff_dashboard_returns_their_tickets(self):
        # Authenticate the client
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
        self.client.force_authenticate(user=self.staff1)
        response = self.client.get('/api/staff/dashboard/')
        data = response.json()
        ticket_ids = [t['id'] for t in data]
        self.assertNotIn(self.other_ticket.id, ticket_ids)

    def test_closed_filter(self):
        self.client.force_authenticate(user=self.staff1)
        response = self.client.get('/api/staff/dashboard/?filtering=closed')
        data = response.json()
        ticket_ids = [t['id'] for t in data]
        ticket_id = self.ticket3.id
        self.assertIn(ticket_id, ticket_ids)

    def test_overdue_filter(self):
        self.client.force_authenticate(user=self.staff1)
        response = self.client.get('/api/staff/dashboard/?filtering=overdue')
        data = response.json()
        ticket_ids = [t['id'] for t in data]
        ticket_id = self.ticket4.id
        self.assertNotIn(ticket_id, ticket_ids)

    def test_all_filter(self):
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
        # Verify structure includes closed_by_role field
        self.assertTrue(all('closed_by_role' in ticket for ticket in data))

    def test_open_filter_all_statuses(self):
        """Test that 'open' filter includes all open status types"""
        # Create tickets with different open statuses
        new_ticket = Ticket.objects.create(
            user=self.student,
            type_of_issue='Software',
            department='IT',
            additional_details='New ticket',
            status=Ticket.Status.NEW,
            assigned_to=self.staff1
        )
        seen_ticket = Ticket.objects.create(
            user=self.student,
            type_of_issue='Software',
            department='IT',
            additional_details='Seen ticket',
            status=Ticket.Status.SEEN,
            assigned_to=self.staff1
        )
        awaiting_ticket = Ticket.objects.create(
            user=self.student,
            type_of_issue='Software',
            department='IT',
            additional_details='Awaiting response',
            status=Ticket.Status.AWAITING_RESPONSE,
            assigned_to=self.staff1
        )
        
        self.client.force_authenticate(user=self.staff1)
        response = self.client.get('/api/staff/dashboard/?filtering=open')
        data = response.json()
        ticket_ids = [t['id'] for t in data]
        
        # All open status tickets should be included
        self.assertIn(self.ticket1.id, ticket_ids)  # PENDING
        self.assertIn(self.ticket2.id, ticket_ids)  # PENDING (IN_PROGRESS)
        self.assertIn(new_ticket.id, ticket_ids)
        self.assertIn(seen_ticket.id, ticket_ids)
        self.assertIn(awaiting_ticket.id, ticket_ids)
        # Closed ticket should NOT be included
        self.assertNotIn(self.ticket3.id, ticket_ids)

    def test_open_filter_explicitly(self):
        """Test that 'open' filter explicitly shows open statuses"""
        # This tests the filter branch explicitly
        self.client.force_authenticate(user=self.staff1)
        response = self.client.get('/api/staff/dashboard/?filtering=open')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        # Should have 2 open tickets (PENDING status)
        self.assertGreater(len(data), 0)

    def test_invalid_filter_defaults_to_open(self):
        """Test that invalid filter value defaults to 'open' behavior"""
        self.client.force_authenticate(user=self.staff1)
        response = self.client.get('/api/staff/dashboard/?filtering=invalid_filter')
        data = response.json()
        
        # Should return tickets (falling through to default)
        self.assertGreater(len(data), 0)

    def test_overdue_filter_empty_for_new_tickets(self):
        """Test that overdue filter excludes recently created tickets"""
        self.client.force_authenticate(user=self.staff1)
        response = self.client.get('/api/staff/dashboard/?filtering=overdue')
        data = response.json()
        ticket_ids = [t['id'] for t in data]
        
        # All current tickets are new (created today), so none should be overdue
        self.assertEqual(len(ticket_ids), 0)

    def test_serializer_includes_is_overdue_field(self):
        """Test that is_overdue field is included in serializer response"""
        self.client.force_authenticate(user=self.staff1)
        response = self.client.get('/api/staff/dashboard/?filtering=all')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # All tickets should have is_overdue field (True or False)
        for ticket in data:
            self.assertIn('is_overdue', ticket)
            self.assertIsInstance(ticket['is_overdue'], bool)

    def test_closed_by_role_field_for_closed_ticket(self):
        """Test that closed_by_role field returns correct role for closed ticket"""
        # Create a closed ticket with closed_by set
        closed_ticket = Ticket.objects.create(
            user=self.student,
            type_of_issue='Software',
            department='IT',
            additional_details='Ticket closed by staff',
            status=Ticket.Status.CLOSED,
            assigned_to=self.staff1,
            closed_by=self.staff1
        )
        
        self.client.force_authenticate(user=self.staff1)
        response = self.client.get('/api/staff/dashboard/?filtering=all')
        data = response.json()
        
        # Find the closed ticket
        closed_ticket_data = next((t for t in data if t['id'] == closed_ticket.id), None)
        self.assertIsNotNone(closed_ticket_data)
        self.assertEqual(closed_ticket_data['closed_by_role'], 'staff')

    def test_closed_by_role_is_null_for_open_ticket(self):
        """Test that closed_by_role is None for open tickets"""
        self.client.force_authenticate(user=self.staff1)
        response = self.client.get('/api/staff/dashboard/?filtering=open')
        data = response.json()
        
        # All open tickets should have closed_by_role as None
        for ticket in data:
            self.assertIsNone(ticket['closed_by_role'])

    def test_closed_by_role_is_null_when_closed_by_not_set(self):
        """Test that closed_by_role is None even for closed tickets without closed_by user"""
        self.client.force_authenticate(user=self.staff1)
        response = self.client.get('/api/staff/dashboard/?filtering=all')
        data = response.json()
        
        # ticket3 is closed but has no closed_by set
        ticket3_data = next((t for t in data if t['id'] == self.ticket3.id), None)
        self.assertIsNotNone(ticket3_data)
        self.assertIsNone(ticket3_data['closed_by_role'])

    def test_search_with_whitespace_only(self):
        """Test that search with whitespace-only string is treated as no search"""
        self.client.force_authenticate(user=self.staff1)
        # Search with spaces should be stripped and treated as empty
        response = self.client.get('/api/staff/dashboard/?search=   ')
        data = response.json()
        ticket_ids = [t['id'] for t in data]
        
        # Should return all assigned tickets (same as no search)
        self.assertEqual(len(ticket_ids), 3)

    def test_search_filters_by_first_name(self):
        """Test that search correctly filters by first name"""
        self.client.force_authenticate(user=self.staff1)
        response = self.client.get('/api/staff/dashboard/?search=Test')
        data = response.json()
        
        # Should only include tickets from 'Test User'
        for ticket in data:
            self.assertEqual(ticket['user']['first_name'], 'Test')

    def test_search_filters_by_last_name(self):
        """Test that search correctly filters by last name"""
        self.client.force_authenticate(user=self.staff1)
        response = self.client.get('/api/staff/dashboard/?search=Student')
        data = response.json()
        
        # Should only include tickets from 'Other Student'
        for ticket in data:
            self.assertEqual(ticket['user']['last_name'], 'Student')

    def test_superuser_can_access_staff_dashboard(self):
        """Test that superuser can access staff dashboard even without staff role"""
        superuser = User.objects.create_user(
            username='superuser',
            email='superuser@example.com',
            password='password123',
            k_number='SU123456',
            is_superuser=True
        )
        self.client.force_authenticate(user=superuser)
        response = self.client.get('/api/staff/dashboard/')
        # Superuser should get 200 OK (no access error)
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_default_filter_is_open(self):
        """Test that default filter (no filtering param) is 'open'"""
        # ticket3 is closed, ticket1 and ticket2 are pending (open)
        self.client.force_authenticate(user=self.staff1)
        response = self.client.get('/api/staff/dashboard/')
        data = response.json()
        ticket_ids = [t['id'] for t in data]
        
        # Should show open tickets by default
        self.assertIn(self.ticket1.id, ticket_ids)
        self.assertIn(self.ticket2.id, ticket_ids)
        self.assertNotIn(self.ticket3.id, ticket_ids)

    def test_closed_filter_excludes_open_tickets(self):
        """Test that closed filter doesn't include open tickets"""
        self.client.force_authenticate(user=self.staff1)
        response = self.client.get('/api/staff/dashboard/?filtering=closed')
        data = response.json()
        ticket_ids = [t['id'] for t in data]
        
        # Should only have closed tickets
        self.assertNotIn(self.ticket1.id, ticket_ids)
        self.assertNotIn(self.ticket2.id, ticket_ids)
        self.assertIn(self.ticket3.id, ticket_ids)

    def test_search_empty_string_treated_as_no_search(self):
        """Test that empty search string returns all tickets"""
        self.client.force_authenticate(user=self.staff1)
        # Empty search should return same results as no search
        response_no_search = self.client.get('/api/staff/dashboard/')
        response_empty_search = self.client.get('/api/staff/dashboard/?search=')
        
        # Should return same result count
        self.assertEqual(len(response_no_search.json()), len(response_empty_search.json()))
