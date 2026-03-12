"""
Tests for the close ticket feature:
- Student can close their own ticket (POST /api/dashboard/tickets/<id>/close/)
- Staff can close tickets assigned to them (PATCH /api/staff/dashboard/<id>/update/)
- closed_by and closed_by_role are set correctly
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from ..models.ticket import Ticket
from ..models.user import User


class StudentCloseTicketTest(TestCase):
    """Test cases for student close ticket endpoint (POST /api/dashboard/tickets/<id>/close/)"""

    def setUp(self):
        self.client = APIClient()
        self.student = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='testpass123',
            k_number='11111111',
            role=User.Role.STUDENT,
        )
        self.other_student = User.objects.create_user(
            username='other_student',
            email='other@test.com',
            password='testpass123',
            k_number='22222222',
            role=User.Role.STUDENT,
        )
        self.ticket = Ticket.objects.create(
            user=self.student,
            department='Informatics',
            type_of_issue='Software Issue',
            additional_details='Need help',
            status=Ticket.Status.PENDING,
        )
        self.other_ticket = Ticket.objects.create(
            user=self.other_student,
            department='Math',
            type_of_issue='Hardware Issue',
            additional_details='Broken laptop',
            status=Ticket.Status.PENDING,
        )

    def test_student_close_own_ticket_success(self):
        """Student can close their own ticket"""
        self.client.force_authenticate(user=self.student)
        url = f'/api/dashboard/tickets/{self.ticket.id}/close/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['status'], 'closed')
        self.assertEqual(response.data['closed_by_role'], 'student')

        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.CLOSED)
        self.assertEqual(self.ticket.closed_by_id, self.student.id)

    def test_student_cannot_close_other_students_ticket(self):
        """Student cannot close another student's ticket"""
        self.client.force_authenticate(user=self.student)
        url = f'/api/dashboard/tickets/{self.other_ticket.id}/close/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.other_ticket.refresh_from_db()
        self.assertEqual(self.other_ticket.status, Ticket.Status.PENDING)
        self.assertIsNone(self.other_ticket.closed_by_id)

    def test_student_close_unauthenticated(self):
        """Unauthenticated request returns 401"""
        url = f'/api/dashboard/tickets/{self.ticket.id}/close/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_close_already_closed(self):
        """Closing an already closed ticket returns 400"""
        self.ticket.status = Ticket.Status.CLOSED
        self.ticket.closed_by = self.student
        self.ticket.save()

        self.client.force_authenticate(user=self.student)
        url = f'/api/dashboard/tickets/{self.ticket.id}/close/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_student_close_nonexistent_ticket(self):
        """Closing non-existent ticket returns 404"""
        self.client.force_authenticate(user=self.student)
        response = self.client.post('/api/dashboard/tickets/99999/close/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class StaffCloseTicketTest(TestCase):
    """Test cases for staff close ticket (PATCH /api/staff/dashboard/<id>/update/)"""

    def setUp(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            k_number='33333333',
            role=User.Role.STAFF,
        )
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            k_number='99999999',
            role=User.Role.ADMIN,
        )
        self.student = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='testpass123',
            k_number='11111111',
            role=User.Role.STUDENT,
        )
        self.other_staff = User.objects.create_user(
            username='other_staff',
            email='otherstaff@test.com',
            password='testpass123',
            k_number='44444444',
            role=User.Role.STAFF,
        )

        self.ticket_assigned_to_staff = Ticket.objects.create(
            user=self.student,
            department='Informatics',
            type_of_issue='Software Issue',
            additional_details='Need help',
            status=Ticket.Status.PENDING,
            assigned_to=self.staff,
        )
        self.ticket_assigned_to_other = Ticket.objects.create(
            user=self.student,
            department='Math',
            type_of_issue='Hardware Issue',
            additional_details='Broken',
            status=Ticket.Status.PENDING,
            assigned_to=self.other_staff,
        )
        self.unassigned_ticket = Ticket.objects.create(
            user=self.student,
            department='Physics',
            type_of_issue='Lab Issue',
            additional_details='Equipment',
            status=Ticket.Status.PENDING,
            assigned_to=None,
        )

    def test_staff_close_assigned_ticket_success(self):
        """Staff can close ticket assigned to them"""
        self.client.force_authenticate(user=self.staff)
        url = f'/api/staff/dashboard/{self.ticket_assigned_to_staff.id}/update/'
        response = self.client.patch(url, {'status': 'closed'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'closed')
        self.assertEqual(response.data['closed_by_role'], 'staff')

        self.ticket_assigned_to_staff.refresh_from_db()
        self.assertEqual(self.ticket_assigned_to_staff.status, Ticket.Status.CLOSED)
        self.assertEqual(self.ticket_assigned_to_staff.closed_by_id, self.staff.id)

    def test_staff_cannot_close_ticket_assigned_to_other(self):
        """Staff cannot close ticket assigned to another staff member"""
        self.client.force_authenticate(user=self.staff)
        url = f'/api/staff/dashboard/{self.ticket_assigned_to_other.id}/update/'
        response = self.client.patch(url, {'status': 'closed'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.ticket_assigned_to_other.refresh_from_db()
        self.assertEqual(self.ticket_assigned_to_other.status, Ticket.Status.PENDING)
        self.assertIsNone(self.ticket_assigned_to_other.closed_by_id)

    def test_staff_cannot_close_unassigned_ticket(self):
        """Staff cannot close unassigned ticket (not assigned to them)"""
        self.client.force_authenticate(user=self.staff)
        url = f'/api/staff/dashboard/{self.unassigned_ticket.id}/update/'
        response = self.client.patch(url, {'status': 'closed'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_close_any_ticket(self):
        """Admin can close any ticket regardless of assignment"""
        self.client.force_authenticate(user=self.admin)
        url = f'/api/staff/dashboard/{self.ticket_assigned_to_staff.id}/update/'
        response = self.client.patch(url, {'status': 'closed'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'closed')
        self.assertEqual(response.data['closed_by_role'], 'admin')

        self.ticket_assigned_to_staff.refresh_from_db()
        self.assertEqual(self.ticket_assigned_to_staff.closed_by_id, self.admin.id)

    def test_staff_close_unauthenticated(self):
        """Unauthenticated request returns 401"""
        url = f'/api/staff/dashboard/{self.ticket_assigned_to_staff.id}/update/'
        response = self.client.patch(url, {'status': 'closed'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_cannot_use_staff_close_endpoint(self):
        """Student cannot use staff ticket update endpoint"""
        self.client.force_authenticate(user=self.student)
        url = f'/api/staff/dashboard/{self.ticket_assigned_to_staff.id}/update/'
        response = self.client.patch(url, {'status': 'closed'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UserDashboardClosedByRoleTest(TestCase):
    """Test that user dashboard includes closed_by_role for closed tickets"""

    def setUp(self):
        self.client = APIClient()
        self.student = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='testpass123',
            k_number='11111111',
            role=User.Role.STUDENT,
        )
        self.ticket_closed_by_student = Ticket.objects.create(
            user=self.student,
            department='Informatics',
            type_of_issue='Issue',
            additional_details='Details',
            status=Ticket.Status.CLOSED,
            closed_by=self.student,
        )

    def test_user_dashboard_includes_closed_by_role(self):
        """User dashboard returns closed_by_role for closed tickets"""
        self.client.force_authenticate(user=self.student)
        response = self.client.get('/api/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tickets = response.data.get('tickets', [])
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0]['status'], 'closed')
        self.assertEqual(tickets[0]['closed_by_role'], 'student')
