from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status

from ..models.ticket import Ticket
from ..models.user import User
from ..models.reply import Reply


class AdminTicketStatisticsTest(TestCase):
    """Test cases for admin ticket statistics endpoint"""

    def _create_users(self):
        self.admin = User.objects.create_user(
            username='admin', email='admin@test.com', password='testpass123',
            k_number='99999999', role=User.Role.ADMIN, is_superuser=True
        )
        self.student = User.objects.create_user(
            username='student', email='student@test.com', password='testpass123',
            k_number='11111111', role=User.Role.STUDENT
        )
        self.staff = User.objects.create_user(
            username='staff', email='staff@test.com', password='testpass123',
            k_number='22222222', role=User.Role.STAFF
        )

    def _seed_department_tickets(self, now):
        for i in range(5):
            created_at = now - timedelta(days=i * 10)
            Ticket.objects.create(
                user=self.student, department='Informatics', type_of_issue='Software Issue',
                additional_details=f'Test ticket {i}',
                status=Ticket.Status.PENDING if i % 2 == 0 else Ticket.Status.RESOLVED,
                priority=Ticket.Priority.MEDIUM if i % 2 == 0 else Ticket.Priority.HIGH,
                created_at=created_at, updated_at=created_at + timedelta(hours=i * 2),
            )
        for i in range(3):
            created_at = now - timedelta(days=i * 15)
            Ticket.objects.create(
                user=self.student, department='Engineering', type_of_issue='Hardware Issue',
                additional_details=f'Engineering ticket {i}',
                status=Ticket.Status.IN_PROGRESS if i % 2 == 0 else Ticket.Status.CLOSED,
                priority=Ticket.Priority.LOW if i == 0 else Ticket.Priority.URGENT,
                created_at=created_at, updated_at=created_at + timedelta(hours=i * 3),
            )
        for i in range(2):
            created_at = now - timedelta(days=i * 5)
            Ticket.objects.create(
                user=self.student, department='Medicine', type_of_issue='Access Issue',
                additional_details=f'Medicine ticket {i}',
                status=Ticket.Status.PENDING, priority=Ticket.Priority.MEDIUM,
                created_at=created_at, updated_at=created_at + timedelta(hours=i),
            )

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.url = '/api/admin/statistics/'
        now = timezone.now()
        self._create_users()
        self._seed_department_tickets(now)

    def test_statistics_unauthenticated(self):
        """Test that unauthenticated users cannot access statistics"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_statistics_non_admin(self):
        """Test that non-admin users cannot access statistics"""
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_statistics_staff_no_access(self):
        """Test that staff users cannot access statistics"""
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_statistics_success(self):
        """Test successful statistics retrieval with default parameters"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_tickets', response.data)
        self.assertIn('department_statistics', response.data)
        self.assertIn('date_range', response.data)

    def test_statistics_default_30_days(self):
        """Test that default statistics returns last 30 days"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should get tickets from last 30 days (not the ones older than 30 days)
        self.assertGreaterEqual(response.data['total_tickets'], 5)

    def test_statistics_custom_days_parameter(self):
        """Test statistics with custom days parameter"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {'days': 7})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only get tickets from last 7 days
        self.assertLessEqual(response.data['total_tickets'], 10)

    def test_statistics_date_range_filter(self):
        """Test statistics with custom date range"""
        self.client.force_authenticate(user=self.admin)
        
        # Get tickets from last 20 days
        end_date = timezone.now()
        start_date = end_date - timedelta(days=20)
        
        response = self.client.get(self.url, {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['date_range']['start_date'], start_date.isoformat())
        self.assertEqual(response.data['date_range']['end_date'], end_date.isoformat())

    def test_statistics_department_breakdown(self):
        """Test that statistics include department breakdown"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dept_stats = response.data['department_statistics']
        
        # Should have stats for multiple departments
        self.assertGreater(len(dept_stats), 0)
        
        # Each department should have required fields
        for dept in dept_stats:
            self.assertIn('department', dept)
            self.assertIn('total_tickets', dept)
            self.assertIn('status_breakdown', dept)
            self.assertIn('priority_breakdown', dept)

    def test_statistics_status_breakdown(self):
        """Test that statistics include status breakdown"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dept_stats = response.data['department_statistics']
        
        for dept in dept_stats:
            status_breakdown = dept['status_breakdown']
            self.assertIn('pending', status_breakdown)
            self.assertIn('in_progress', status_breakdown)
            self.assertIn('resolved', status_breakdown)
            self.assertIn('closed', status_breakdown)

    def test_statistics_priority_breakdown(self):
        """Test that statistics include priority breakdown"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dept_stats = response.data['department_statistics']
        
        for dept in dept_stats:
            priority_breakdown = dept['priority_breakdown']
            self.assertIn('low', priority_breakdown)
            self.assertIn('medium', priority_breakdown)
            self.assertIn('high', priority_breakdown)
            self.assertIn('urgent', priority_breakdown)

    def test_statistics_avg_resolution_time(self):
        """Test that statistics include average resolution time"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dept_stats = response.data['department_statistics']
        
        for dept in dept_stats:
            # avg_resolution_time_hours can be null if no closed tickets
            self.assertIn('avg_resolution_time_hours', dept)

    def test_statistics_invalid_days_parameter(self):
        """Test statistics with invalid days parameter"""
        self.client.force_authenticate(user=self.admin)
        
        # Test with negative days
        response = self.client.get(self.url, {'days': -5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        
        # Test with zero days
        response = self.client.get(self.url, {'days': 0})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test with non-integer days
        response = self.client.get(self.url, {'days': 'abc'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_statistics_invalid_date_format(self):
        """Test statistics with invalid date format"""
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.get(self.url, {
            'start_date': 'invalid-date',
            'end_date': 'invalid-date'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_statistics_ordered_by_total_tickets(self):
        """Test that departments are ordered by total ticket count"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dept_stats = response.data['department_statistics']
        
        # Check that departments are sorted by total_tickets (descending)
        if len(dept_stats) > 1:
            for i in range(len(dept_stats) - 1):
                self.assertGreaterEqual(
                    dept_stats[i]['total_tickets'],
                    dept_stats[i + 1]['total_tickets']
                )

    def test_statistics_empty_date_range(self):
        """Test statistics with date range that has no tickets"""
        self.client.force_authenticate(user=self.admin)
        
        # Use a future date range
        start_date = timezone.now() + timedelta(days=10)
        end_date = timezone.now() + timedelta(days=20)
        
        response = self.client.get(self.url, {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_tickets'], 0)
        self.assertEqual(len(response.data['department_statistics']), 0)

    def test_statistics_single_department(self):
        """Test statistics calculation for a single department"""
        self.client.force_authenticate(user=self.admin)
        
        # Get statistics for a short period that might have tickets from only one department
        response = self.client.get(self.url, {'days': 3})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should work even with limited data
        self.assertIn('department_statistics', response.data)


class AdminAvgResponseTimeTest(TestCase):
    """Test cases for average staff response time in statistics"""

    def _create_users(self):
        self.admin = User.objects.create_user(
            username='admin', email='admin@test.com', password='testpass123',
            k_number='99999999', role=User.Role.ADMIN, is_superuser=True,
        )
        self.staff = User.objects.create_user(
            username='staff', email='staff@test.com', password='testpass123',
            k_number='22222222', role=User.Role.STAFF,
        )
        self.student = User.objects.create_user(
            username='student', email='student@test.com', password='testpass123',
            k_number='11111111', role=User.Role.STUDENT,
        )

    def _create_informatics_ticket_with_response(self, now, issue, details, status, created_hours_ago, reply_hours):
        ticket = Ticket.objects.create(
            user=self.student, department='Informatics',
            type_of_issue=issue, additional_details=details, status=status,
        )
        Ticket.objects.filter(id=ticket.id).update(created_at=now - timedelta(hours=created_hours_ago))
        ticket.refresh_from_db()
        staff_reply = Reply.objects.create(user=self.staff, ticket=ticket, body='Staff reply')
        Reply.objects.filter(id=staff_reply.id).update(created_at=ticket.created_at + timedelta(hours=reply_hours))
        return ticket

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/admin/statistics/'
        self._create_users()
        now = timezone.now()
        self.ticket1 = self._create_informatics_ticket_with_response(
            now, 'Software Issue', 'Help', Ticket.Status.PENDING, 4, 2
        )
        Reply.objects.create(user=self.student, ticket=self.ticket1, body='Student note')
        self.ticket2 = self._create_informatics_ticket_with_response(
            now, 'Hardware Issue', 'Broken', Ticket.Status.IN_PROGRESS, 6, 4
        )

        # Ticket with no staff reply
        self.ticket3 = Ticket.objects.create(
            user=self.student, department='Engineering',
            type_of_issue='Lab Issue', additional_details='Equipment',
            status=Ticket.Status.PENDING,
        )

    def test_avg_response_time_field_present(self):
        """Statistics include avg_response_time_hours field"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for dept in response.data['department_statistics']:
            self.assertIn('avg_response_time_hours', dept)

    def test_avg_response_time_calculated_correctly(self):
        """Average response time is the mean of first-staff-reply deltas"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        dept_map = {d['department']: d for d in response.data['department_statistics']}

        # Informatics: (2h + 4h) / 2 = 3h
        info = dept_map.get('Informatics')
        self.assertIsNotNone(info)
        self.assertIsNotNone(info['avg_response_time_hours'])
        self.assertAlmostEqual(info['avg_response_time_hours'], 3.0, delta=0.1)

    def test_avg_response_time_null_when_no_staff_replies(self):
        """Departments with no staff replies have null avg_response_time_hours"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        dept_map = {d['department']: d for d in response.data['department_statistics']}
        eng = dept_map.get('Engineering')
        self.assertIsNotNone(eng)
        self.assertIsNone(eng['avg_response_time_hours'])

    def test_avg_response_time_ignores_student_replies(self):
        """Only staff/admin replies count for response time, not student replies"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        dept_map = {d['department']: d for d in response.data['department_statistics']}
        info = dept_map.get('Informatics')
        # If student replies were counted, the avg would be much lower than 3h
        self.assertAlmostEqual(info['avg_response_time_hours'], 3.0, delta=0.1)


class AdminUserDetailTest(TestCase):
    """Test cases for admin user detail endpoint"""

    def _create_admin_and_user(self):
        self.admin = User.objects.create_user(
            username='admin', email='admin@test.com', password='testpass123',
            k_number='99999999', role=User.Role.ADMIN, is_superuser=True
        )
        self.test_user = User.objects.create_user(
            username='testuser', email='testuser@test.com', password='testpass123',
            first_name='John', last_name='Doe', k_number='12345678',
            department='Informatics', role=User.Role.STUDENT
        )

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self._create_admin_and_user()
        self.url = f'/api/admin/users/{self.test_user.id}/'

    def test_user_detail_unauthenticated(self):
        """Test that unauthenticated users cannot access user detail"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_detail_non_admin(self):
        """Test that non-admin users cannot access user detail"""
        self.client.force_authenticate(user=self.test_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_detail_success(self):
        """Test successful user detail retrieval"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.test_user.id)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'testuser@test.com')
        self.assertEqual(response.data['first_name'], 'John')
        self.assertEqual(response.data['last_name'], 'Doe')
        self.assertEqual(response.data['k_number'], '12345678')
        self.assertEqual(response.data['department'], 'Informatics')
        self.assertEqual(response.data['role'], 'student')

    def test_user_detail_not_found(self):
        """Test user detail with non-existent user ID"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/admin/users/99999/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_user_detail_includes_role_flags(self):
        """Test that user detail includes role flags"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('is_staff', response.data)
        self.assertIn('is_superuser', response.data)
        self.assertFalse(response.data['is_staff'])
        self.assertFalse(response.data['is_superuser'])

    def test_user_detail_admin_user(self):
        """Test user detail for an admin user"""
        self.client.force_authenticate(user=self.admin)
        url = f'/api/admin/users/{self.admin.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'admin')
        self.assertTrue(response.data['is_superuser'])
