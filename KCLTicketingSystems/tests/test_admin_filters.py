from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from ..models.ticket import Ticket
from ..models.user import User


class AdminTicketsAdvancedFilterTest(TestCase):
    """Test cases for advanced filtering scenarios in admin tickets list"""

    def _create_users(self):
        self.admin = User.objects.create_user(
            username='admin', email='admin@test.com', password='testpass123',
            k_number='99999999', role=User.Role.ADMIN, is_superuser=True
        )
        self.staff1 = User.objects.create_user(
            username='staff1', email='staff1@test.com', password='testpass123',
            first_name='Alice', last_name='Staff', k_number='22222222', role=User.Role.STAFF
        )
        self.staff2 = User.objects.create_user(
            username='staff2', email='staff2@test.com', password='testpass123',
            first_name='Bob', last_name='Staff', k_number='33333333', role=User.Role.STAFF
        )
        self.student1 = User.objects.create_user(
            username='student1', email='student1@test.com', password='testpass123',
            first_name='Charlie', last_name='Student', k_number='11111111', role=User.Role.STUDENT
        )
        self.student2 = User.objects.create_user(
            username='student2', email='student2@test.com', password='testpass123',
            first_name='Diana', last_name='Student', k_number='44444444', role=User.Role.STUDENT
        )

    def _create_tickets(self):
        self.ticket1 = Ticket.objects.create(
            user=self.student1, department='Informatics', type_of_issue='Software Issue',
            additional_details='Need help with Python', status=Ticket.Status.PENDING,
            priority=Ticket.Priority.MEDIUM
        )
        self.ticket2 = Ticket.objects.create(
            user=self.student1, department='Informatics', type_of_issue='Network Issue',
            additional_details='Cannot connect to VPN', status=Ticket.Status.IN_PROGRESS,
            priority=Ticket.Priority.HIGH, assigned_to=self.staff1
        )
        self.ticket3 = Ticket.objects.create(
            user=self.student2, department='Engineering', type_of_issue='Hardware Issue',
            additional_details='Laptop not working', status=Ticket.Status.PENDING,
            priority=Ticket.Priority.URGENT, assigned_to=self.staff1
        )
        self.ticket4 = Ticket.objects.create(
            user=self.student2, department='Engineering', type_of_issue='Access Issue',
            additional_details='Cannot access lab', status=Ticket.Status.RESOLVED,
            priority=Ticket.Priority.LOW, assigned_to=self.staff2
        )
        self.ticket5 = Ticket.objects.create(
            user=self.student1, department='Medicine', type_of_issue='Database Issue',
            additional_details='Cannot query patient records', status=Ticket.Status.CLOSED,
            priority=Ticket.Priority.HIGH
        )

    def _create_unassigned_ticket(self):
        self.ticket6 = Ticket.objects.create(
            user=self.student2, department='Informatics', type_of_issue='Email Issue',
            additional_details='Email not working', status=Ticket.Status.PENDING,
            priority=Ticket.Priority.MEDIUM
        )

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.url = '/api/admin/tickets/'
        self._create_users()
        self._create_tickets()
        self._create_unassigned_ticket()

    def test_filter_unassigned_tickets(self):
        """Test filtering for unassigned tickets"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {'assigned_to': 'unassigned'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tickets = response.data['tickets']
        
        # Should return tickets without assignment
        self.assertGreater(len(tickets), 0)
        for ticket in tickets:
            self.assertIsNone(ticket['assigned_to'])

    def test_filter_by_specific_staff(self):
        """Test filtering tickets assigned to a specific staff member"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {'assigned_to': self.staff1.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tickets = response.data['tickets']
        
        # Should return only tickets assigned to staff1
        self.assertGreater(len(tickets), 0)
        for ticket in tickets:
            self.assertEqual(ticket['assigned_to'], self.staff1.id)

    def test_combine_status_and_priority_filters(self):
        """Test combining status and priority filters"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {
            'status': 'pending',
            'priority': 'urgent'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tickets = response.data['tickets']
        
        # Should return only pending urgent tickets
        for ticket in tickets:
            self.assertEqual(ticket['status'], 'pending')
            self.assertEqual(ticket['priority'], 'urgent')

    def test_combine_department_and_assigned_filters(self):
        """Test combining department and assigned_to filters"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {
            'department': 'Engineering',
            'assigned_to': self.staff1.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tickets = response.data['tickets']
        
        # Should return only Engineering tickets assigned to staff1
        self.assertGreater(len(tickets), 0)
        for ticket in tickets:
            self.assertEqual(ticket['department'], 'Engineering')
            self.assertEqual(ticket['assigned_to'], self.staff1.id)

    def test_combine_search_with_filters(self):
        """Test combining search query with other filters"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {
            'search': 'Charlie',
            'status': 'in_progress'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tickets = response.data['tickets']
        
        # Should return tickets from Charlie that are in progress
        for ticket in tickets:
            self.assertEqual(ticket['status'], 'in_progress')

    def test_combine_all_filters(self):
        """Test combining all available filters"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {
            'search': 'Student',
            'status': 'pending',
            'priority': 'medium',
            'department': 'Informatics',
            'assigned_to': 'unassigned'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tickets = response.data['tickets']
        
        # Should apply all filters
        for ticket in tickets:
            self.assertEqual(ticket['status'], 'pending')
            self.assertEqual(ticket['priority'], 'medium')
            self.assertEqual(ticket['department'], 'Informatics')
            self.assertIsNone(ticket['assigned_to'])

    def test_filter_with_no_results(self):
        """Test filters that return no results"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {
            'status': 'pending',
            'department': 'Nonexistent'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tickets = response.data['tickets']
        self.assertEqual(len(tickets), 0)
        self.assertEqual(response.data['total'], 0)

    def test_pagination_with_filters(self):
        """Test that pagination works correctly with filters"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {
            'status': 'pending',
            'page': 1,
            'page_size': 2
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total', response.data)
        self.assertIn('page', response.data)
        self.assertIn('page_size', response.data)
        self.assertEqual(response.data['page'], 1)
        self.assertEqual(response.data['page_size'], 2)

    def test_search_by_k_number(self):
        """Test searching tickets by user k-number"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {'search': '11111111'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tickets = response.data['tickets']
        
        # Should return tickets from user with k-number 11111111
        self.assertGreater(len(tickets), 0)
        for ticket in tickets:
            self.assertEqual(ticket['user_k_number'], '11111111')

    def test_search_by_email(self):
        """Test searching tickets by user email"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {'search': 'student1@test.com'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tickets = response.data['tickets']
        
        # Should return tickets from user with that email
        self.assertGreater(len(tickets), 0)

    def test_search_by_issue_type(self):
        """Test searching tickets by type of issue"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {'search': 'Network'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tickets = response.data['tickets']
        
        # Should return tickets with "Network" in issue type
        self.assertGreater(len(tickets), 0)

    def test_case_insensitive_search(self):
        """Test that search is case-insensitive"""
        self.client.force_authenticate(user=self.admin)
        
        # Search with lowercase
        response1 = self.client.get(self.url, {'search': 'charlie'})
        # Search with uppercase
        response2 = self.client.get(self.url, {'search': 'CHARLIE'})
        # Search with mixed case
        response3 = self.client.get(self.url, {'search': 'ChArLiE'})
        
        # All should return same results
        self.assertEqual(
            len(response1.data['tickets']),
            len(response2.data['tickets'])
        )
        self.assertEqual(
            len(response2.data['tickets']),
            len(response3.data['tickets'])
        )

    def test_filter_different_priorities(self):
        """Test filtering by each priority level"""
        self.client.force_authenticate(user=self.admin)
        
        priorities = ['low', 'medium', 'high', 'urgent']
        
        for priority in priorities:
            response = self.client.get(self.url, {'priority': priority})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            tickets = response.data['tickets']
            for ticket in tickets:
                self.assertEqual(ticket['priority'], priority)

    def test_filter_different_statuses(self):
        """Test filtering by each status"""
        self.client.force_authenticate(user=self.admin)
        
        statuses = ['pending', 'in_progress', 'resolved', 'closed']
        
        for status_value in statuses:
            response = self.client.get(self.url, {'status': status_value})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            tickets = response.data['tickets']
            for ticket in tickets:
                self.assertEqual(ticket['status'], status_value)

    def test_filter_by_department(self):
        """Test filtering by different departments"""
        self.client.force_authenticate(user=self.admin)
        departments = ['Informatics', 'Engineering', 'Medicine']
        for department in departments:
            response = self.client.get(self.url, {'department': department})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            tickets = response.data['tickets']
            self.assertTrue(
                all(ticket['department'] == department for ticket in tickets),
                f"Found ticket outside {department}",
            )

    def test_multiple_unassigned_tickets(self):
        """Test that multiple unassigned tickets are returned correctly"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {'assigned_to': 'unassigned'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tickets = response.data['tickets']
        
        # Count unassigned tickets
        unassigned_count = len([t for t in tickets if t['assigned_to'] is None])
        self.assertGreater(unassigned_count, 0)


class AdminUsersAdvancedFilterTest(TestCase):
    """Test cases for advanced filtering in admin users list"""

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
            role=User.Role.ADMIN,
            is_superuser=True
        )
        
        # Create users with different roles and departments
        for i in range(10):
            User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@test.com',
                password='testpass123',
                first_name=f'User{i}',
                last_name='Test',
                k_number=f'1000000{i:02d}',
                department='Informatics' if i % 3 == 0 else 'Engineering',
                role=User.Role.STUDENT if i % 2 == 0 else User.Role.STAFF
            )

    def test_filter_users_by_role(self):
        """Test filtering users by role"""
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.get(self.url, {'role': 'student'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        users = response.data['users']
        for user in users:
            self.assertEqual(user['role'], 'student')

    def test_search_users_by_username(self):
        """Test searching users by username"""
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.get(self.url, {'search': 'user1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        users = response.data['users']
        self.assertGreater(len(users), 0)

    def test_search_users_by_k_number(self):
        """Test searching users by k-number"""
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.get(self.url, {'search': '10000000'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        users = response.data['users']
        self.assertGreater(len(users), 0)

    def test_search_users_by_email(self):
        """Test searching users by email"""
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.get(self.url, {'search': 'user2@test.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        users = response.data['users']
        self.assertGreater(len(users), 0)

    def test_combine_search_and_role_filter(self):
        """Test combining search with role filter"""
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.get(self.url, {
            'search': 'user',
            'role': 'staff'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        users = response.data['users']
        for user in users:
            self.assertEqual(user['role'], 'staff')

    def test_users_pagination_with_filters(self):
        """Test that pagination works with user filters"""
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.get(self.url, {
            'role': 'student',
            'page': 1,
            'page_size': 3
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['page'], 1)
        self.assertEqual(response.data['page_size'], 3)
        self.assertLessEqual(len(response.data['users']), 3)

    def test_case_insensitive_user_search(self):
        """Test that user search is case-insensitive"""
        self.client.force_authenticate(user=self.admin)
        
        response1 = self.client.get(self.url, {'search': 'user'})
        response2 = self.client.get(self.url, {'search': 'USER'})
        
        # Should return same number of results
        self.assertEqual(
            len(response1.data['users']),
            len(response2.data['users'])
        )


class AdminTicketBoundaryTest(TestCase):
    """Test boundary conditions and edge cases for admin ticket management"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            k_number='99999999',
            role=User.Role.ADMIN,
            is_superuser=True
        )
        
        # Create test user
        self.student = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='testpass123',
            k_number='11111111',
            role=User.Role.STUDENT
        )

    def test_pagination_first_page(self):
        """Test first page of pagination"""
        self.client.force_authenticate(user=self.admin)
        
        # Create some tickets
        for i in range(5):
            Ticket.objects.create(
                user=self.student,
                department='Informatics',
                type_of_issue='Test Issue',
                additional_details=f'Ticket {i}'
            )
        
        response = self.client.get('/api/admin/tickets/', {'page': 1, 'page_size': 3})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['page'], 1)
        self.assertEqual(len(response.data['tickets']), 3)

    def test_pagination_last_page(self):
        """Test last page of pagination with partial results"""
        self.client.force_authenticate(user=self.admin)
        
        # Create 7 tickets
        for i in range(7):
            Ticket.objects.create(
                user=self.student,
                department='Informatics',
                type_of_issue='Test Issue',
                additional_details=f'Ticket {i}'
            )
        
        response = self.client.get('/api/admin/tickets/', {'page': 3, 'page_size': 3})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['page'], 3)
        # Last page should have 1 ticket (7 % 3 = 1)
        self.assertEqual(len(response.data['tickets']), 1)

    def test_pagination_beyond_last_page(self):
        """Test requesting page beyond the last page"""
        self.client.force_authenticate(user=self.admin)
        
        # Create 5 tickets
        for i in range(5):
            Ticket.objects.create(
                user=self.student,
                department='Informatics',
                type_of_issue='Test Issue',
                additional_details=f'Ticket {i}'
            )
        
        response = self.client.get('/api/admin/tickets/', {'page': 10, 'page_size': 3})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return empty list
        self.assertEqual(len(response.data['tickets']), 0)

    def test_empty_database(self):
        """Test admin endpoints with no tickets"""
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.get('/api/admin/tickets/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 0)
        self.assertEqual(len(response.data['tickets']), 0)

    def test_large_page_size(self):
        """Test with very large page size"""
        self.client.force_authenticate(user=self.admin)
        
        # Create 10 tickets
        for i in range(10):
            Ticket.objects.create(
                user=self.student,
                department='Informatics',
                type_of_issue='Test Issue',
                additional_details=f'Ticket {i}'
            )
        
        response = self.client.get('/api/admin/tickets/', {'page_size': 1000})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return all tickets
        self.assertEqual(len(response.data['tickets']), 10)
