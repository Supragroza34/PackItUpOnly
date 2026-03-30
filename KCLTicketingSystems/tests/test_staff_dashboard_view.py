from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from KCLTicketingSystems.models import Ticket, Reply, User
from django.db import models
from django.utils import timezone
from datetime import timedelta, datetime


class StaffDashboardViewTests(TestCase):

    DASHBOARD_URL = "/api/staff/dashboard/"

    def setUp(self):
        self.client = APIClient()
        self._create_users()
        self._create_staff_members()
        self._create_base_tickets()
        self._create_replies_for_ticket1()
        self.other_ticket = self._create_ticket(
            user=self.student2,
            assigned_to=self.staff2,
            type_of_issue="Network",
            department="IT",
            additional_details="Other user ticket",
            status="open",
        )

    def _create_users(self):
        self.student = User.objects.create_user(
            first_name="Test",
            last_name="User",
            username="testuser",
            email="testuser@example.com",
            password="password123",
            k_number="K123456",
        )
        self.student2 = User.objects.create_user(
            first_name="Other",
            last_name="Student",
            username="otherstudent",
            email="otherstudent@example.com",
            password="password123",
            k_number="K654321",
        )

    def _create_staff_members(self):
        self.staff1 = User.objects.create_user(
            username="staff1",
            email="staff1@example.com",
            password="password123",
            k_number="S654321",
            role=User.Role.STAFF,
        )
        self.staff2 = User.objects.create_user(
            username="staff2",
            email="staff2@example.com",
            password="password123",
            k_number="S123456",
            role=User.Role.STAFF,
        )

    def _create_ticket(self, user, assigned_to, type_of_issue, department, additional_details, status):
        return Ticket.objects.create(
            user=user,
            type_of_issue=type_of_issue,
            department=department,
            additional_details=additional_details,
            status=status,
            assigned_to=assigned_to,
        )

    def _create_base_tickets(self):
        self._create_primary_assigned_tickets()
        self._create_additional_status_tickets()

    def _create_primary_assigned_tickets(self):
        self.ticket1 = self._create_ticket(
            user=self.student,
            assigned_to=self.staff1,
            type_of_issue="Software",
            department="IT",
            additional_details="Issue details 1",
            status=Ticket.Status.PENDING,
        )
        self.ticket2 = self._create_ticket(
            user=self.student,
            assigned_to=self.staff1,
            type_of_issue="Hardware",
            department="Maintenance",
            additional_details="Issue details 2",
            status=Ticket.Status.PENDING,
        )

    def _create_additional_status_tickets(self):
        self.ticket3 = self._create_ticket(
            user=self.student,
            assigned_to=self.staff1,
            type_of_issue="Software",
            department="IT",
            additional_details="Issue details 1",
            status=Ticket.Status.CLOSED,
        )
        self.ticket4 = self._create_ticket(
            user=self.student,
            assigned_to=self.staff1,
            type_of_issue="Software",
            department="IT",
            additional_details="Issue details 1",
            status=Ticket.Status.IN_PROGRESS,
        )

    def _create_open_status_tickets(self):
        new_ticket = self._create_ticket(
            user=self.student,
            assigned_to=self.staff1,
            type_of_issue="Software",
            department="IT",
            additional_details="New ticket",
            status=Ticket.Status.NEW,
        )
        seen_ticket = self._create_ticket(
            user=self.student,
            assigned_to=self.staff1,
            type_of_issue="Software",
            department="IT",
            additional_details="Seen ticket",
            status=Ticket.Status.SEEN,
        )
        awaiting_ticket = self._create_ticket(
            user=self.student,
            assigned_to=self.staff1,
            type_of_issue="Software",
            department="IT",
            additional_details="Awaiting response",
            status=Ticket.Status.AWAITING_RESPONSE,
        )
        return [new_ticket, seen_ticket, awaiting_ticket]

    def _assert_open_filter_contains_expected_tickets(self, ticket_ids, dynamic_open_tickets):
        self.assertIn(self.ticket1.id, ticket_ids)
        self.assertIn(self.ticket2.id, ticket_ids)
        for ticket in dynamic_open_tickets:
            self.assertIn(ticket.id, ticket_ids)
        self.assertNotIn(self.ticket3.id, ticket_ids)

    def _create_replies_for_ticket1(self):
        self.reply1 = Reply.objects.create(ticket=self.ticket1, user=self.staff1, body="Reply 1")
        self.reply2 = Reply.objects.create(ticket=self.ticket1, user=self.staff1, body="Reply 2")

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def _dashboard_response(self, query=""):
        return self.client.get(f"{self.DASHBOARD_URL}{query}")

    def _ticket_ids(self, response):
        return [ticket["id"] for ticket in response.json()]

    def test_dashboard_requires_authentication(self):
        response = self._dashboard_response()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_staff_returns_access_error(self):
        self._auth(self.student)
        response = self._dashboard_response()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_staff_dashboard_returns_their_tickets(self):
        self._auth(self.staff1)
        response = self._dashboard_response()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ticket_ids = self._ticket_ids(response)
        self.assertEqual(len(ticket_ids), 3)
        self.assertIn(self.ticket1.id, ticket_ids)
        self.assertIn(self.ticket2.id, ticket_ids)

    def test_staff_cannot_see_others_staff_tickets(self):
        self._auth(self.staff1)
        response = self._dashboard_response()
        ticket_ids = self._ticket_ids(response)
        self.assertNotIn(self.other_ticket.id, ticket_ids)

    def test_closed_filter(self):
        self._auth(self.staff1)
        response = self._dashboard_response("?filtering=closed")
        self.assertIn(self.ticket3.id, self._ticket_ids(response))

    def test_overdue_filter(self):
        self._auth(self.staff1)
        response = self._dashboard_response("?filtering=overdue")
        self.assertNotIn(self.ticket4.id, self._ticket_ids(response))

    def test_all_filter(self):
        self._auth(self.staff1)
        response = self._dashboard_response("?filtering=all")
        ticket_ids = self._ticket_ids(response)
        self.assertIn(self.ticket1.id, ticket_ids)
        self.assertIn(self.ticket2.id, ticket_ids)
        self.assertIn(self.ticket3.id, ticket_ids)
        self.assertIn(self.ticket4.id, ticket_ids)

    def test_search_bar(self):
        self.other_ticket2 = Ticket.objects.create(
            user=self.student2,
            type_of_issue='Network',
            department='IT',
            additional_details='Other user ticket',
            status='open',
            assigned_to=self.staff1
        )
        self._auth(self.staff1)
        response = self._dashboard_response('?filtering=closed&search=Test')
        ticket_ids = self._ticket_ids(response)
        self.assertIn(self.ticket3.id, ticket_ids)
        self.assertNotIn(self.ticket2.id, ticket_ids)
        self.assertNotIn(self.other_ticket2.id, ticket_ids)

        response_2 = self._dashboard_response('?filtering=all&search=Other')
        ticket_ids_2 = self._ticket_ids(response_2)
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

        self._auth(self.staff1)
        response = self._dashboard_response('?filtering=all')
        data = response.json()

    def test_closed_by_role_fallback(self):
        self.ticket3.closed_by = self.staff1
        self.ticket3.save()
        self.client.force_authenticate(user=self.staff1)
        response = self.client.get('/api/staff/dashboard/?filtering=closed')
        data = response.json()
        ticket = next(t for t in data if t['id'] == self.ticket3.id)
        self.assertEqual(ticket['closed_by_role'], 'staff')
        self.assertTrue(all('closed_by_role' in ticket for ticket in data))

    def test_open_filter_all_statuses(self):
        """Test that 'open' filter includes all open status types"""
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
        
        self.assertIn(self.ticket1.id, ticket_ids)  
        self.assertIn(self.ticket2.id, ticket_ids)  
        self.assertIn(new_ticket.id, ticket_ids)
        self.assertIn(seen_ticket.id, ticket_ids)
        self.assertIn(awaiting_ticket.id, ticket_ids)
        self.assertNotIn(self.ticket3.id, ticket_ids)

    def test_open_filter_explicitly(self):
        """Test that 'open' filter explicitly shows open statuses"""
        self.client.force_authenticate(user=self.staff1)
        response = self.client.get('/api/staff/dashboard/?filtering=open')
        dynamic_open_tickets = self._create_open_status_tickets()
        self._auth(self.staff1)
        response = self._dashboard_response('?filtering=open')
        ticket_ids = self._ticket_ids(response)
        self._assert_open_filter_contains_expected_tickets(ticket_ids, dynamic_open_tickets)

    def test_open_filter_explicitly(self):
        """Test that 'open' filter explicitly shows open statuses"""
        self._auth(self.staff1)
        response = self._dashboard_response('?filtering=open')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertGreater(len(data), 0)

    def test_invalid_filter_defaults_to_open(self):
        """Test that invalid filter value defaults to 'open' behavior"""
        self._auth(self.staff1)
        response = self._dashboard_response('?filtering=invalid_filter')
        data = response.json()
        self.assertGreater(len(data), 0)

    def test_overdue_filter_empty_for_new_tickets(self):
        """Test that overdue filter excludes recently created tickets"""
        self._auth(self.staff1)
        response = self._dashboard_response('?filtering=overdue')
        ticket_ids = self._ticket_ids(response)
        self.assertEqual(len(ticket_ids), 0)

    def test_serializer_includes_is_overdue_field(self):
        """Test that is_overdue field is included in serializer response"""
        self._auth(self.staff1)
        response = self._dashboard_response('?filtering=all')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
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
        
        self._auth(self.staff1)
        response = self._dashboard_response('?filtering=all')
        data = response.json()
        closed_ticket_data = next((t for t in data if t['id'] == closed_ticket.id), None)
        self.assertIsNotNone(closed_ticket_data)
        self.assertEqual(closed_ticket_data['closed_by_role'], 'staff')

    def test_closed_by_role_is_null_for_open_ticket(self):
        """Test that closed_by_role is None for open tickets"""
        self._auth(self.staff1)
        response = self._dashboard_response('?filtering=open')
        data = response.json()
        for ticket in data:
            self.assertIsNone(ticket['closed_by_role'])

    def test_closed_by_role_is_null_when_closed_by_not_set(self):
        """Test that closed_by_role is None even for closed tickets without closed_by user"""
        self._auth(self.staff1)
        response = self._dashboard_response('?filtering=all')
        data = response.json()
        ticket3_data = next((t for t in data if t['id'] == self.ticket3.id), None)
        self.assertIsNotNone(ticket3_data)
        self.assertIsNone(ticket3_data['closed_by_role'])

    def test_search_with_whitespace_only(self):
        """Test that search with whitespace-only string is treated as no search"""
        self._auth(self.staff1)
        response = self._dashboard_response('?search=   ')
        ticket_ids = self._ticket_ids(response)
        self.assertEqual(len(ticket_ids), 3)

    def test_search_filters_by_first_name(self):
        """Test that search correctly filters by first name"""
        self._auth(self.staff1)
        response = self._dashboard_response('?search=Test')
        data = response.json()
        for ticket in data:
            self.assertEqual(ticket['user']['first_name'], 'Test')

    def test_search_filters_by_last_name(self):
        """Test that search correctly filters by last name"""
        self._auth(self.staff1)
        response = self._dashboard_response('?search=Student')
        data = response.json()
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
        self._auth(superuser)
        response = self._dashboard_response()
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_default_filter_is_open(self):
        """Test that default filter (no filtering param) is 'open'"""
        self._auth(self.staff1)
        response = self._dashboard_response()
        ticket_ids = self._ticket_ids(response)
        self.assertIn(self.ticket1.id, ticket_ids)
        self.assertIn(self.ticket2.id, ticket_ids)
        self.assertNotIn(self.ticket3.id, ticket_ids)

    def test_closed_filter_excludes_open_tickets(self):
        """Test that closed filter doesn't include open tickets"""
        self._auth(self.staff1)
        response = self._dashboard_response('?filtering=closed')
        ticket_ids = self._ticket_ids(response)
        self.assertNotIn(self.ticket1.id, ticket_ids)
        self.assertNotIn(self.ticket2.id, ticket_ids)
        self.assertIn(self.ticket3.id, ticket_ids)

    def test_search_empty_string_treated_as_no_search(self):
        """Test that empty search string returns all tickets"""
        self._auth(self.staff1)
        response_no_search = self._dashboard_response()
        response_empty_search = self._dashboard_response('?search=')
        self.assertEqual(len(response_no_search.json()), len(response_empty_search.json()))
