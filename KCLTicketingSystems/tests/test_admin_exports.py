import csv
import io
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status

from ..models.ticket import Ticket
from ..models.user import User


class AdminExportStatisticsCSVTest(TestCase):
    """Test cases for admin statistics CSV export endpoint. This keeps regressions visible early in the release cycle."""

    def _create_base_users(self):
        """Support the admin exports tests by create base users so assertions remain focused on outcomes."""
        self.admin = User.objects.create_user(
            username='admin', email='admin@test.com', password='testpass123',
            k_number='99999999', role=User.Role.ADMIN, is_superuser=True
        )
        self.student = User.objects.create_user(
            username='student', email='student@test.com', password='testpass123',
            k_number='11111111', role=User.Role.STUDENT
        )

    def _create_department_tickets(self, now):
        """Support the admin exports tests by create department tickets so assertions remain focused on outcomes."""
        for i in range(5):
            Ticket.objects.create(
                user=self.student, department='Informatics', type_of_issue='Software Issue',
                additional_details=f'Test ticket {i}',
                status=Ticket.Status.PENDING if i % 2 == 0 else Ticket.Status.CLOSED,
                priority=Ticket.Priority.MEDIUM if i % 2 == 0 else Ticket.Priority.HIGH,
                created_at=now - timedelta(days=i),
                updated_at=now - timedelta(days=i) + timedelta(hours=i),
            )
        for i in range(3):
            Ticket.objects.create(
                user=self.student, department='Engineering', type_of_issue='Hardware Issue',
                additional_details=f'Engineering ticket {i}',
                status=Ticket.Status.IN_PROGRESS if i % 2 == 0 else Ticket.Status.RESOLVED,
                priority=Ticket.Priority.LOW if i == 0 else Ticket.Priority.URGENT,
                created_at=now - timedelta(days=i * 2),
                updated_at=now - timedelta(days=i * 2) + timedelta(hours=i),
            )

    def setUp(self):
        """Set up test data. This keeps regressions visible early in the release cycle."""
        self.client = APIClient()
        self.url = '/api/admin/export/statistics-csv/'
        now = timezone.now()
        self._create_base_users()
        self._create_department_tickets(now)

    def test_export_statistics_unauthenticated(self):
        """Test that unauthenticated users cannot export statistics. This keeps regressions visible early in the release cycle."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_export_statistics_non_admin(self):
        """Test that non-admin users cannot export statistics. This keeps regressions visible early in the release cycle."""
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_export_statistics_success(self):
        """Test successful statistics CSV export. This keeps regressions visible early in the release cycle."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('ticket_statistics', response['Content-Disposition'])

    def test_export_statistics_csv_headers(self):
        """Test that CSV export includes correct headers. This keeps regressions visible early in the release cycle."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        
        # Parse CSV content
        content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))
        headers = next(csv_reader)
        
        expected_headers = [
            'Department',
            'Total Tickets',
            'Pending',
            'In Progress',
            'Resolved',
            'Closed',
            'Low Priority',
            'Medium Priority',
            'High Priority',
            'Urgent Priority',
            'Avg Resolution Time (hours)',
            'Avg Response Time (hours)'
        ]
        
        self.assertEqual(headers, expected_headers)

    def test_export_statistics_csv_data(self):
        """Test that CSV export includes correct data. This keeps regressions visible early in the release cycle."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        
        # Parse CSV content
        content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))
        
        # Skip header
        next(csv_reader)
        
        # Read data rows
        rows = list(csv_reader)
        
        # Should have data for departments
        self.assertGreater(len(rows), 0)
        
        # Check that each row has correct number of columns
        for row in rows:
            self.assertEqual(len(row), 12)  # 12 columns as per headers

    def test_export_statistics_custom_days(self):
        """Test statistics export with custom days parameter. This keeps regressions visible early in the release cycle."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {'days': 7})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')

    def test_export_statistics_date_range(self):
        """Test statistics export with custom date range. This keeps regressions visible early in the release cycle."""
        self.client.force_authenticate(user=self.admin)
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=20)
        
        response = self.client.get(self.url, {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('Content-Disposition', response)
        # Filename should include date range
        filename = response['Content-Disposition']
        self.assertIn(str(start_date.date()), filename)
        self.assertIn(str(end_date.date()), filename)

    def test_export_statistics_invalid_days(self):
        """Test statistics export with invalid days parameter. This keeps regressions visible early in the release cycle."""
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.get(self.url, {'days': -5})
        self.assertEqual(response.status_code, 400)
        
        response = self.client.get(self.url, {'days': 'abc'})
        self.assertEqual(response.status_code, 400)

    def test_export_statistics_invalid_date_format(self):
        """Test statistics export with invalid date format. This keeps regressions visible early in the release cycle."""
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.get(self.url, {
            'start_date': 'invalid-date',
            'end_date': 'invalid-date'
        })
        
        self.assertEqual(response.status_code, 400)

    def test_export_statistics_department_names(self):
        """Test that exported CSV contains correct department names. This keeps regressions visible early in the release cycle."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        
        content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))
        next(csv_reader)  # Skip header
        
        rows = list(csv_reader)
        departments = [row[0] for row in rows]
        
        # Should include our test departments
        self.assertIn('Informatics', departments)
        self.assertIn('Engineering', departments)


class AdminExportTicketsCSVTest(TestCase):
    """Test cases for admin tickets CSV export endpoint. This keeps regressions visible early in the release cycle."""

    def _create_users(self):
        """Support the admin exports tests by create users so assertions remain focused on outcomes."""
        self.admin = User.objects.create_user(
            username='admin', email='admin@test.com', password='testpass123',
            k_number='99999999', role=User.Role.ADMIN, is_superuser=True
        )
        self.staff = User.objects.create_user(
            username='staff', email='staff@test.com', password='testpass123',
            first_name='Staff', last_name='Member', k_number='22222222', role=User.Role.STAFF
        )
        self.student1 = User.objects.create_user(
            username='student1', email='student1@test.com', password='testpass123',
            first_name='John', last_name='Doe', k_number='11111111', role=User.Role.STUDENT
        )
        self.student2 = User.objects.create_user(
            username='student2', email='student2@test.com', password='testpass123',
            first_name='Jane', last_name='Smith', k_number='33333333', role=User.Role.STUDENT
        )

    def _create_tickets(self):
        """Support the admin exports tests by create tickets so assertions remain focused on outcomes."""
        self.ticket1 = Ticket.objects.create(
            user=self.student1, department='Informatics', type_of_issue='Software Issue',
            additional_details='Test ticket 1', status=Ticket.Status.PENDING, priority=Ticket.Priority.MEDIUM
        )
        self.ticket2 = Ticket.objects.create(
            user=self.student2, department='Engineering', type_of_issue='Hardware Issue',
            additional_details='Test ticket 2', status=Ticket.Status.IN_PROGRESS,
            priority=Ticket.Priority.HIGH, assigned_to=self.staff
        )
        self.ticket3 = Ticket.objects.create(
            user=self.student1, department='Medicine', type_of_issue='Access Issue',
            additional_details='Test ticket 3', status=Ticket.Status.RESOLVED, priority=Ticket.Priority.LOW
        )

    def _create_old_ticket(self):
        """Support the admin exports tests by create old ticket so assertions remain focused on outcomes."""
        old_ticket = Ticket.objects.create(
            department='Law', type_of_issue='General Inquiry', additional_details='Old ticket',
            status='pending', priority='low', user=self.student1
        )
        old_ticket.created_at = timezone.now() - timedelta(days=40)
        old_ticket.save()

    def setUp(self):
        """Set up test data. This keeps regressions visible early in the release cycle."""
        self.client = APIClient()
        self.url = '/api/admin/export/tickets-csv/'
        self._create_users()
        self._create_tickets()

    def test_export_tickets_unauthenticated(self):
        """Test that unauthenticated users cannot export tickets. This keeps regressions visible early in the release cycle."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_export_tickets_non_admin(self):
        """Test that non-admin users cannot export tickets. This keeps regressions visible early in the release cycle."""
        self.client.force_authenticate(user=self.student1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_export_tickets_success(self):
        """Test successful tickets CSV export. This keeps regressions visible early in the release cycle."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('tickets', response['Content-Disposition'])

    def test_export_tickets_csv_headers(self):
        """Test that CSV export includes correct headers. This keeps regressions visible early in the release cycle."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        
        # Parse CSV content
        content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))
        headers = next(csv_reader)
        
        # Check that all expected headers are present
        expected_headers = [
            'Ticket ID', 'Department', 'Issue Type', 'Status', 'Priority',
            'Created Date', 'Updated Date', 'User K-Number', 'User Name',
            'User Email', 'Assigned To', 'Additional Details', 'Admin Notes'
        ]
        
        self.assertEqual(headers, expected_headers)

    def test_export_tickets_csv_data(self):
        """Test that CSV export includes all tickets. This keeps regressions visible early in the release cycle."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        
        # Parse CSV content
        content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))
        
        # Skip header
        next(csv_reader)
        
        # Read data rows
        rows = list(csv_reader)
        
        # Should have all tickets
        self.assertEqual(len(rows), 3)
        
        # Check that each row has correct number of columns (13 columns)
        for row in rows:
            self.assertEqual(len(row), 13)

    def test_export_tickets_date_range_filter(self):
        """Test tickets export with date range filter. This keeps regressions visible early in the release cycle."""
        self.client.force_authenticate(user=self.admin)
        self._create_old_ticket()
        # Export only last 30 days (should not include old ticket)
        response = self.client.get(self.url, {'days': '30'})
        
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))
        next(csv_reader)
        
        rows = list(csv_reader)
        # Should only have 3 recent tickets, not the old one
        self.assertEqual(len(rows), 3)

    def test_export_tickets_custom_days(self):
        """Test tickets export with custom days parameter. This keeps regressions visible early in the release cycle."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {'days': '7'})
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response['Content-Disposition'])

    def test_export_tickets_invalid_days(self):
        """Test tickets export with invalid days parameter. This keeps regressions visible early in the release cycle."""
        self.client.force_authenticate(user=self.admin)
        
        # Test with negative days
        response = self.client.get(self.url, {'days': '-5'})
        self.assertEqual(response.status_code, 400)
        
        # Test with non-integer days
        response = self.client.get(self.url, {'days': 'abc'})
        self.assertEqual(response.status_code, 400)

    def test_export_tickets_empty_result(self):
        """Test tickets export with date range that returns no results. This keeps regressions visible early in the release cycle."""
        self.client.force_authenticate(user=self.admin)
        
        # Request tickets from 100 days ago to 60 days ago
        from django.utils import timezone
        from datetime import timedelta
        
        end_date = (timezone.now() - timedelta(days=60)).isoformat()
        start_date = (timezone.now() - timedelta(days=100)).isoformat()
        
        response = self.client.get(self.url, {
            'start_date': start_date,
            'end_date': end_date
        })
        
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))
        next(csv_reader)
        
        rows = list(csv_reader)
        # Should have no tickets in this date range
        self.assertEqual(len(rows), 0)
