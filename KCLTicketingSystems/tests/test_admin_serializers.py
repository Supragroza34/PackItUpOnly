from django.test import TestCase
from rest_framework.test import APIRequestFactory

from ..serializers import (
    UserSerializer,
    RegisterSerializer,
    TicketSerializer,
    TicketListSerializer,
    TicketUpdateSerializer,
    DashboardStatsSerializer
)
from ..models.user import User
from ..models.ticket import Ticket


class UserSerializerTest(TestCase):
    """Test cases for UserSerializer"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            k_number='12345678',
            first_name='Test',
            last_name='User',
            department='Informatics',
            role=User.Role.STUDENT
        )

    def test_user_serializer_fields(self):
        """Test that UserSerializer returns correct fields"""
        serializer = UserSerializer(self.user)
        
        expected_fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'k_number', 'department', 'role', 'is_staff', 'is_superuser'
        ]
        
        self.assertEqual(set(serializer.data.keys()), set(expected_fields))

    def test_user_serializer_data(self):
        """Test that UserSerializer returns correct data"""
        serializer = UserSerializer(self.user)
        
        self.assertEqual(serializer.data['username'], 'testuser')
        self.assertEqual(serializer.data['email'], 'test@test.com')
        self.assertEqual(serializer.data['k_number'], '12345678')
        self.assertEqual(serializer.data['role'], 'student')
        self.assertFalse(serializer.data['is_staff'])
        self.assertFalse(serializer.data['is_superuser'])

    def test_user_serializer_admin_flags(self):
        """Test UserSerializer with admin user"""
        admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            k_number='99999999',
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True
        )
        
        serializer = UserSerializer(admin)
        
        self.assertEqual(serializer.data['role'], 'admin')
        self.assertTrue(serializer.data['is_staff'])
        self.assertTrue(serializer.data['is_superuser'])

    def test_user_serializer_read_only_fields(self):
        """Test that read-only fields cannot be updated"""
        serializer = UserSerializer(self.user, data={
            'is_staff': True,
            'is_superuser': True
        }, partial=True)
        
        # Should be valid but read-only fields ignored
        self.assertTrue(serializer.is_valid())
        
        # Meta should define read-only fields
        self.assertIn('is_staff', UserSerializer.Meta.read_only_fields)
        self.assertIn('is_superuser', UserSerializer.Meta.read_only_fields)

    def test_user_serializer_multiple_users(self):
        """Test serializing multiple users"""
        user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='testpass123',
            k_number='87654321',
            role=User.Role.STAFF
        )
        
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        
        self.assertEqual(len(serializer.data), 2)


class RegisterSerializerTest(TestCase):
    """Test cases for RegisterSerializer"""

    def setUp(self):
        """Set up test data"""
        self.valid_data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'testpass123',
            'k_number': '12345678',
            'first_name': 'New',
            'last_name': 'User',
            'department': 'Informatics'
        }

    def test_register_serializer_valid_data(self):
        """Test RegisterSerializer with valid data"""
        serializer = RegisterSerializer(data=self.valid_data)
        
        self.assertTrue(serializer.is_valid())

    def test_register_serializer_create_user(self):
        """Test that RegisterSerializer creates user correctly"""
        serializer = RegisterSerializer(data=self.valid_data)
        
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'newuser@test.com')
        self.assertEqual(user.k_number, '12345678')
        self.assertTrue(user.check_password('testpass123'))  # Password hashed
        self.assertEqual(user.role, User.Role.STUDENT)  # Default role

    def test_register_serializer_password_hashing(self):
        """Test that password is properly hashed"""
        serializer = RegisterSerializer(data=self.valid_data)
        
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        
        # Password should be hashed, not plain text
        self.assertNotEqual(user.password, 'testpass123')
        self.assertTrue(user.password.startswith('pbkdf2_sha256'))

    def test_register_serializer_password_write_only(self):
        """Test that password is write-only"""
        serializer = RegisterSerializer(data=self.valid_data)
        
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        
        # Re-serialize the user
        output_serializer = RegisterSerializer(user)
        
        # Password should not be in output
        self.assertNotIn('password', output_serializer.data)

    def test_register_serializer_short_password(self):
        """Test that short password is rejected"""
        data = self.valid_data.copy()
        data['password'] = 'short'
        
        serializer = RegisterSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_register_serializer_missing_required_fields(self):
        """Test that missing required fields are rejected"""
        # k_number is not required as it has blank=True in the model
        required_fields = ['username', 'email', 'password']
        
        for field in required_fields:
            data = self.valid_data.copy()
            del data[field]
            
            serializer = RegisterSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn(field, serializer.errors)

    def test_register_serializer_duplicate_username(self):
        """Test that duplicate username is rejected"""
        # Create first user
        User.objects.create_user(
            username='newuser',
            email='other@test.com',
            password='testpass123',
            k_number='87654321'
        )
        
        # Try to create another with same username
        serializer = RegisterSerializer(data=self.valid_data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)


class TicketSerializerTest(TestCase):
    """Test cases for TicketSerializer"""

    def setUp(self):
        """Set up test data"""
        # Create ticket user
        self.ticket_user = User.objects.create_user(
            username='ticketuser',
            email='ticketuser@test.com',
            password='testpass123',
            k_number='12345678',
            first_name='John',
            last_name='Doe',
            role=User.Role.STUDENT
        )
        
        self.staff = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            k_number='99999999',
            first_name='Staff',
            last_name='Member',
            role=User.Role.STAFF
        )
        
        self.ticket = Ticket.objects.create(
            user=self.ticket_user,
            department='Informatics',
            type_of_issue='Software Installation Issues',
            additional_details='Need help',
            status=Ticket.Status.PENDING,
            priority=Ticket.Priority.MEDIUM,
            assigned_to=self.staff
        )

    def test_ticket_serializer_fields(self):
        """Test that TicketSerializer includes all fields"""
        serializer = TicketSerializer(self.ticket)
        
        # Should include all model fields plus user_details and assigned_to_details
        self.assertIn('id', serializer.data)
        self.assertIn('user', serializer.data)
        self.assertIn('user_details', serializer.data)
        self.assertIn('assigned_to', serializer.data)
        self.assertIn('assigned_to_details', serializer.data)

    def test_ticket_serializer_assigned_to_details(self):
        """Test that assigned_to_details is nested UserSerializer"""
        serializer = TicketSerializer(self.ticket)
        
        self.assertIsNotNone(serializer.data['assigned_to_details'])
        self.assertEqual(serializer.data['assigned_to_details']['username'], 'staff')
        self.assertEqual(serializer.data['assigned_to_details']['first_name'], 'Staff')

    def test_ticket_serializer_unassigned(self):
        """Test TicketSerializer with unassigned ticket"""
        user = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='testpass123',
            k_number='87654321',
            first_name='Jane',
            last_name='Smith',
            role=User.Role.STUDENT
        )
        ticket = Ticket.objects.create(
            user=user,
            department='Engineering',
            type_of_issue='Hardware Issues',
            additional_details='Hardware problem'
        )
        
        serializer = TicketSerializer(ticket)
        
        self.assertIsNone(serializer.data['assigned_to'])
        self.assertIsNone(serializer.data['assigned_to_details'])

    def test_ticket_serializer_read_only_fields(self):
        """Test that created_at and updated_at are read-only"""
        self.assertIn('created_at', TicketSerializer.Meta.read_only_fields)
        self.assertIn('updated_at', TicketSerializer.Meta.read_only_fields)


class TicketListSerializerTest(TestCase):
    """Test cases for TicketListSerializer"""

    def setUp(self):
        """Set up test data"""
        # Create ticket user
        self.ticket_user = User.objects.create_user(
            username='ticketuser',
            email='ticketuser@test.com',
            password='testpass123',
            k_number='12345678',
            first_name='John',
            last_name='Doe',
            role=User.Role.STUDENT
        )
        
        self.staff = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            k_number='99999999',
            first_name='Staff',
            last_name='Member',
            role=User.Role.STAFF
        )
        
        self.ticket = Ticket.objects.create(
            user=self.ticket_user,
            department='Informatics',
            type_of_issue='Software Installation Issues',
            additional_details='Test details',
            assigned_to=self.staff
        )

    def test_ticket_list_serializer_fields(self):
        """Test that TicketListSerializer includes correct fields"""
        serializer = TicketListSerializer(self.ticket)
        
        expected_fields = [
            'id', 'user_name', 'user_k_number', 'department',
            'type_of_issue', 'status', 'priority', 'assigned_to_name',
            'created_at', 'updated_at'
        ]
        
        self.assertEqual(set(serializer.data.keys()), set(expected_fields))

    def test_ticket_list_serializer_assigned_to_name(self):
        """Test assigned_to_name method field"""
        serializer = TicketListSerializer(self.ticket)
        
        self.assertEqual(serializer.data['assigned_to_name'], 'Staff Member')

    def test_ticket_list_serializer_unassigned(self):
        """Test assigned_to_name with unassigned ticket"""
        user = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='testpass123',
            k_number='87654321',
            first_name='Jane',
            last_name='Smith',
            role=User.Role.STUDENT
        )
        ticket = Ticket.objects.create(
            user=user,
            department='Engineering',
            type_of_issue='Hardware Issues',
            additional_details='Hardware problem'
        )
        
        serializer = TicketListSerializer(ticket)
        
        self.assertIsNone(serializer.data['assigned_to_name'])

    def test_ticket_list_serializer_multiple_tickets(self):
        """Test serializing multiple tickets"""
        user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='testpass123',
            k_number='87654321',
            first_name='Jane',
            last_name='Smith',
            role=User.Role.STUDENT
        )
        ticket2 = Ticket.objects.create(
            user=user2,
            department='Engineering',
            type_of_issue='Hardware Issues',
            additional_details='Hardware problem'
        )
        
        tickets = Ticket.objects.all()
        serializer = TicketListSerializer(tickets, many=True)
        
        self.assertEqual(len(serializer.data), 2)


class TicketUpdateSerializerTest(TestCase):
    """Test cases for TicketUpdateSerializer"""

    def setUp(self):
        """Set up test data"""
        self.staff = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            k_number='99999999',
            role=User.Role.STAFF
        )

    def test_ticket_update_serializer_fields(self):
        """Test that TicketUpdateSerializer includes only updatable fields"""
        expected_fields = ['status', 'priority', 'assigned_to', 'admin_notes']
        
        self.assertEqual(set(TicketUpdateSerializer.Meta.fields), set(expected_fields))

    def test_ticket_update_serializer_valid_data(self):
        """Test TicketUpdateSerializer with valid data"""
        data = {
            'status': 'in_progress',
            'priority': 'high',
            'assigned_to': self.staff.id,
            'admin_notes': 'Working on it'
        }
        
        serializer = TicketUpdateSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())


class DashboardStatsSerializerTest(TestCase):
    """Test cases for DashboardStatsSerializer"""

    def setUp(self):
        """Set up test data"""
        # Create ticket users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='testpass123',
            k_number='12345678',
            first_name='John',
            last_name='Doe',
            role=User.Role.STUDENT
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='testpass123',
            k_number='87654321',
            first_name='Jane',
            last_name='Smith',
            role=User.Role.STUDENT
        )
        
        # Create some tickets
        self.ticket1 = Ticket.objects.create(
            user=self.user1,
            department='Informatics',
            type_of_issue='Software Installation Issues',
            additional_details='Need help',
            status=Ticket.Status.PENDING
        )
        
        self.ticket2 = Ticket.objects.create(
            user=self.user2,
            department='Engineering',
            type_of_issue='Hardware Issues',
            additional_details='Hardware problem',
            status=Ticket.Status.IN_PROGRESS
        )

    def test_dashboard_stats_serializer_fields(self):
        """Test that DashboardStatsSerializer includes all stat fields"""
        data = {
            'total_tickets': 10,
            'pending_tickets': 3,
            'in_progress_tickets': 2,
            'resolved_tickets': 4,
            'closed_tickets': 1,
            'total_users': 20,
            'total_students': 15,
            'total_staff': 4,
            'total_admins': 1,
            'recent_tickets': []
        }
        
        serializer = DashboardStatsSerializer(data)
        
        expected_fields = [
            'total_tickets', 'pending_tickets', 'in_progress_tickets',
            'resolved_tickets', 'closed_tickets', 'total_users',
            'total_students', 'total_staff', 'total_admins', 'recent_tickets'
        ]
        
        self.assertEqual(set(serializer.data.keys()), set(expected_fields))

    def test_dashboard_stats_serializer_with_recent_tickets(self):
        """Test DashboardStatsSerializer with recent tickets"""
        tickets = Ticket.objects.all()
        
        data = {
            'total_tickets': 2,
            'pending_tickets': 1,
            'in_progress_tickets': 1,
            'resolved_tickets': 0,
            'closed_tickets': 0,
            'total_users': 0,
            'total_students': 0,
            'total_staff': 0,
            'total_admins': 0,
            'recent_tickets': tickets
        }
        
        serializer = DashboardStatsSerializer(data)
        
        self.assertEqual(len(serializer.data['recent_tickets']), 2)
        self.assertIn('id', serializer.data['recent_tickets'][0])

    def test_dashboard_stats_serializer_integer_fields(self):
        """Test that all count fields are integers"""
        data = {
            'total_tickets': 10,
            'pending_tickets': 3,
            'in_progress_tickets': 2,
            'resolved_tickets': 4,
            'closed_tickets': 1,
            'total_users': 20,
            'total_students': 15,
            'total_staff': 4,
            'total_admins': 1,
            'recent_tickets': []
        }
        
        serializer = DashboardStatsSerializer(data)
        
        # All count fields should be integers
        for field in ['total_tickets', 'pending_tickets', 'total_users']:
            self.assertIsInstance(serializer.data[field], int)
