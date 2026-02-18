from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from ..models.ticket import Ticket
from ..models.user import User


class AdminDashboardStatsTest(TestCase):
    """Test cases for admin dashboard statistics endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.url = '/api/admin/dashboard/stats/'
        
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            k_number='99999999',
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True
        )
        
        # Create regular user
        self.student = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='testpass123',
            k_number='11111111',
            role=User.Role.STUDENT
        )
        
        # Create staff user
        self.staff = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            k_number='22222222',
            role=User.Role.STAFF
        )
        
        # Create test tickets
        self.ticket1 = Ticket.objects.create(
            name='John',
            surname='Doe',
            k_number='12345678',
            k_email='K12345678@kcl.ac.uk',
            department='Informatics',
            type_of_issue='Software Installation Issues',
            status=Ticket.Status.PENDING
        )
        
        self.ticket2 = Ticket.objects.create(
            name='Jane',
            surname='Smith',
            k_number='87654321',
            k_email='K87654321@kcl.ac.uk',
            department='Engineering',
            type_of_issue='Hardware Issues',
            status=Ticket.Status.IN_PROGRESS,
            assigned_to=self.staff
        )
        
        self.ticket3 = Ticket.objects.create(
            name='Bob',
            surname='Johnson',
            k_number='11223344',
            k_email='K11223344@kcl.ac.uk',
            department='Mathematics',
            type_of_issue='Network Issues',
            status=Ticket.Status.RESOLVED
        )

    def test_dashboard_stats_unauthenticated(self):
        """Test that unauthenticated users cannot access dashboard stats"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_dashboard_stats_non_admin(self):
        """Test that non-admin users cannot access dashboard stats"""
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_dashboard_stats_success(self):
        """Test successful dashboard stats retrieval"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_tickets', response.data)
        self.assertIn('pending_tickets', response.data)
        self.assertIn('in_progress_tickets', response.data)
        self.assertIn('resolved_tickets', response.data)
        self.assertIn('total_users', response.data)
        self.assertIn('total_students', response.data)
        self.assertIn('total_staff', response.data)
        self.assertIn('total_admins', response.data)

    def test_dashboard_stats_counts(self):
        """Test that dashboard stats return correct counts"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        
        self.assertEqual(response.data['total_tickets'], 3)
        self.assertEqual(response.data['pending_tickets'], 1)
        self.assertEqual(response.data['in_progress_tickets'], 1)
        self.assertEqual(response.data['resolved_tickets'], 1)
        self.assertEqual(response.data['total_users'], 3)
        self.assertEqual(response.data['total_students'], 1)
        self.assertEqual(response.data['total_staff'], 1)
        self.assertEqual(response.data['total_admins'], 1)

    def test_dashboard_stats_staff_access(self):
        """Test that staff users cannot access dashboard stats"""
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminTicketsListTest(TestCase):
    """Test cases for admin tickets list endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.url = '/api/admin/tickets/'
        
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            k_number='99999999',
            role=User.Role.ADMIN
        )
        
        # Create test tickets
        for i in range(25):
            Ticket.objects.create(
                name=f'User{i}',
                surname='Test',
                k_number=f'1000000{i:02d}',
                k_email=f'K1000000{i:02d}@kcl.ac.uk',
                department='Informatics' if i % 2 == 0 else 'Engineering',
                type_of_issue='Software Installation Issues',
                status=Ticket.Status.PENDING if i % 3 == 0 else Ticket.Status.IN_PROGRESS
            )

    def test_tickets_list_unauthenticated(self):
        """Test that unauthenticated users cannot access tickets list"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tickets_list_success(self):
        """Test successful tickets list retrieval"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tickets', response.data)
        self.assertIn('total', response.data)
        self.assertIn('page', response.data)
        self.assertIn('page_size', response.data)
        self.assertIn('total_pages', response.data)

    def test_tickets_list_pagination(self):
        """Test tickets list pagination"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {'page': 1, 'page_size': 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['tickets']), 10)
        self.assertEqual(response.data['total'], 25)
        self.assertEqual(response.data['page'], 1)
        self.assertEqual(response.data['page_size'], 10)
        self.assertEqual(response.data['total_pages'], 3)

    def test_tickets_list_search(self):
        """Test tickets list search functionality"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {'search': 'User0'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should find User0, User10, User20 (all containing 'User0')
        self.assertGreaterEqual(len(response.data['tickets']), 1)

    def test_tickets_list_status_filter(self):
        """Test tickets list status filter"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {'status': 'pending'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for ticket in response.data['tickets']:
            self.assertEqual(ticket['status'], 'pending')

    def test_tickets_list_department_filter(self):
        """Test tickets list department filter"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {'department': 'Informatics'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for ticket in response.data['tickets']:
            self.assertEqual(ticket['department'], 'Informatics')


class AdminTicketDetailTest(TestCase):
    """Test cases for admin ticket detail endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            k_number='99999999',
            role=User.Role.ADMIN
        )
        
        # Create test ticket
        self.ticket = Ticket.objects.create(
            name='John',
            surname='Doe',
            k_number='12345678',
            k_email='K12345678@kcl.ac.uk',
            department='Informatics',
            type_of_issue='Software Installation Issues'
        )
        
        self.url = f'/api/admin/tickets/{self.ticket.id}/'

    def test_ticket_detail_unauthenticated(self):
        """Test that unauthenticated users cannot access ticket detail"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ticket_detail_success(self):
        """Test successful ticket detail retrieval"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'John')
        self.assertEqual(response.data['surname'], 'Doe')
        self.assertEqual(response.data['k_number'], '12345678')

    def test_ticket_detail_not_found(self):
        """Test ticket detail with non-existent ID"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/admin/tickets/99999/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)


class AdminTicketUpdateTest(TestCase):
    """Test cases for admin ticket update endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create users
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            k_number='99999999',
            role=User.Role.ADMIN
        )
        
        self.staff = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            k_number='22222222',
            role=User.Role.STAFF
        )
        
        # Create test ticket
        self.ticket = Ticket.objects.create(
            name='John',
            surname='Doe',
            k_number='12345678',
            k_email='K12345678@kcl.ac.uk',
            department='Informatics',
            type_of_issue='Software Installation Issues',
            status=Ticket.Status.PENDING
        )
        
        self.url = f'/api/admin/tickets/{self.ticket.id}/update/'

    def test_ticket_update_unauthenticated(self):
        """Test that unauthenticated users cannot update tickets"""
        response = self.client.patch(self.url, {'status': 'in_progress'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ticket_update_status(self):
        """Test successful ticket status update"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(self.url, {'status': 'in_progress'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'in_progress')
        
        # Verify in database
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.IN_PROGRESS)

    def test_ticket_update_priority(self):
        """Test ticket priority update"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(self.url, {'priority': 'high'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['priority'], 'high')

    def test_ticket_update_assignment(self):
        """Test ticket assignment to staff"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(self.url, {'assigned_to': self.staff.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['assigned_to'], self.staff.id)
        
        # Verify in database
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.assigned_to_id, self.staff.id)

    def test_ticket_update_admin_notes(self):
        """Test ticket admin notes update"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(self.url, {'admin_notes': 'Test notes'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['admin_notes'], 'Test notes')

    def test_ticket_update_multiple_fields(self):
        """Test updating multiple fields at once"""
        self.client.force_authenticate(user=self.admin)
        update_data = {
            'status': 'in_progress',
            'priority': 'high',
            'assigned_to': self.staff.id,
            'admin_notes': 'Updated ticket'
        }
        response = self.client.patch(self.url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'in_progress')
        self.assertEqual(response.data['priority'], 'high')
        self.assertEqual(response.data['assigned_to'], self.staff.id)
        self.assertEqual(response.data['admin_notes'], 'Updated ticket')

    def test_ticket_update_not_found(self):
        """Test updating non-existent ticket"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch('/api/admin/tickets/99999/update/', {'status': 'resolved'})
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AdminTicketDeleteTest(TestCase):
    """Test cases for admin ticket delete endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            k_number='99999999',
            role=User.Role.ADMIN
        )
        
        # Create test ticket
        self.ticket = Ticket.objects.create(
            name='John',
            surname='Doe',
            k_number='12345678',
            k_email='K12345678@kcl.ac.uk',
            department='Informatics',
            type_of_issue='Software Installation Issues'
        )
        
        self.url = f'/api/admin/tickets/{self.ticket.id}/delete/'

    def test_ticket_delete_unauthenticated(self):
        """Test that unauthenticated users cannot delete tickets"""
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ticket_delete_success(self):
        """Test successful ticket deletion"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
        self.assertTrue(response.data['success'])
        
        # Verify ticket is deleted
        self.assertFalse(Ticket.objects.filter(id=self.ticket.id).exists())

    def test_ticket_delete_not_found(self):
        """Test deleting non-existent ticket"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete('/api/admin/tickets/99999/delete/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AdminUsersListTest(TestCase):
    """Test cases for admin users list endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.url = '/api/admin/users/'
        
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            k_number='99999999',
            role=User.Role.ADMIN
        )
        
        # Create test users
        for i in range(25):
            User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@test.com',
                password='testpass123',
                k_number=f'2000000{i:02d}',
                role=User.Role.STUDENT if i % 2 == 0 else User.Role.STAFF
            )

    def test_users_list_unauthenticated(self):
        """Test that unauthenticated users cannot access users list"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_users_list_success(self):
        """Test successful users list retrieval"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('users', response.data)
        self.assertIn('total', response.data)

    def test_users_list_pagination(self):
        """Test users list pagination"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {'page': 1, 'page_size': 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['users']), 10)
        self.assertEqual(response.data['page'], 1)

    def test_users_list_search(self):
        """Test users list search functionality"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {'search': 'user0'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['users']), 1)

    def test_users_list_role_filter(self):
        """Test users list role filter"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {'role': 'student'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for user in response.data['users']:
            self.assertEqual(user['role'], 'student')


class AdminUserUpdateTest(TestCase):
    """Test cases for admin user update endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            k_number='99999999',
            role=User.Role.ADMIN
        )
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123',
            k_number='11111111',
            role=User.Role.STUDENT
        )
        
        self.url = f'/api/admin/users/{self.user.id}/update/'

    def test_user_update_unauthenticated(self):
        """Test that unauthenticated users cannot update users"""
        response = self.client.patch(self.url, {'role': 'staff'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_update_role(self):
        """Test successful user role update"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(self.url, {'role': 'staff'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'staff')
        
        # Verify in database
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, User.Role.STAFF)

    def test_user_update_multiple_fields(self):
        """Test updating multiple user fields"""
        self.client.force_authenticate(user=self.admin)
        update_data = {
            'role': 'staff',
            'department': 'Engineering',
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        response = self.client.patch(self.url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'staff')
        self.assertEqual(response.data['department'], 'Engineering')
        self.assertEqual(response.data['first_name'], 'Updated')
        self.assertEqual(response.data['last_name'], 'Name')


class AdminUserDeleteTest(TestCase):
    """Test cases for admin user delete endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            k_number='99999999',
            role=User.Role.ADMIN
        )
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123',
            k_number='11111111',
            role=User.Role.STUDENT
        )
        
        self.url = f'/api/admin/users/{self.user.id}/delete/'

    def test_user_delete_unauthenticated(self):
        """Test that unauthenticated users cannot delete users"""
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_delete_success(self):
        """Test successful user deletion"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
        self.assertTrue(response.data['success'])
        
        # Verify user is deleted
        self.assertFalse(User.objects.filter(id=self.user.id).exists())

    def test_user_delete_self(self):
        """Test that admin cannot delete their own account"""
        self.client.force_authenticate(user=self.admin)
        url = f'/api/admin/users/{self.admin.id}/delete/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        
        # Verify admin still exists
        self.assertTrue(User.objects.filter(id=self.admin.id).exists())

    def test_user_delete_not_found(self):
        """Test deleting non-existent user"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete('/api/admin/users/99999/delete/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AdminStaffListTest(TestCase):
    """Test cases for admin staff list endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.url = '/api/admin/staff/'
        
        # Create users with different roles
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            k_number='99999999',
            role=User.Role.ADMIN
        )
        
        self.staff = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            k_number='22222222',
            role=User.Role.STAFF
        )
        
        self.student = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='testpass123',
            k_number='11111111',
            role=User.Role.STUDENT
        )

    def test_staff_list_unauthenticated(self):
        """Test that unauthenticated users cannot access staff list"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_staff_list_success(self):
        """Test successful staff list retrieval"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('staff', response.data)

    def test_staff_list_only_staff_and_admin(self):
        """Test that staff list only includes staff and admin users"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        staff_list = response.data['staff']
        
        # Should include admin and staff, but not student
        self.assertEqual(len(staff_list), 2)
        roles = [user['role'] for user in staff_list]
        self.assertIn('admin', roles)
        self.assertIn('staff', roles)
        self.assertNotIn('student', roles)
