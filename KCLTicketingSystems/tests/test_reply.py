from django.test import TestCase
from datetime import datetime
from KCLTicketingSystems.models import Ticket, Reply, User

class ReplyModelTest(TestCase):
    """Test cases for the Reply model"""

    def setUp(self):
        """Set up test data"""
        # Create a student first
        self.student = User.objects.create_user(
            username='teststudent',
            email='teststudent@test.com',
            password='testpass123',
            first_name='Tester',
            last_name='One',
            k_number='73573402',
            role=User.Role.STUDENT
        )

        # create a ticket by this student (as in test_ticket.py)
        
        self.ticket_data = {
            'user': self.student,
            'department': 'Informatics',
            'type_of_issue': 'Software Installation Issues',
            'additional_details': 'Need help installing Python'
        }

        # create a staff member to reply

        self.staff = User.objects.create_user(
            username='teststaff',
            email='teststaff@test.com',
            password='testpass123',
            first_name='Tester',
            last_name='Two',
            k_number='73573473',
            role=User.Role.STAFF
        )

        ticket = Ticket.objects.create(**self.ticket_data)
        body = "Try switching off and then on again."
        self.reply_data = {
            'user': self.staff,
            'ticket': ticket,
            'body': body,
        }

    def test_reply_creation(self):
        """Test creating a reply"""
        reply = Reply.objects.create(**self.reply_data)
        self.assertEqual(reply.user.role, 'staff')
        self.assertEqual(reply.body, 'Try switching off and then on again.')
        self.assertEqual(reply.ticket.user.first_name, 'Tester')
        self.assertEqual(reply.ticket.user.last_name, 'One')
        self.assertEqual(reply.ticket.user.k_number, '73573402')
        self.assertEqual(reply.ticket.user.email, 'teststudent@test.com')
        self.assertEqual(reply.ticket.department, 'Informatics')
        self.assertEqual(reply.ticket.type_of_issue, 'Software Installation Issues')
        self.assertEqual(reply.ticket.additional_details, 'Need help installing Python')
        self.assertIsNotNone(reply.ticket.created_at)
        self.assertIsNotNone(reply.ticket.updated_at)

    def test_reply_str_method(self):
        """Test the __str__ method of Reply model"""
        reply = Reply.objects.create(**self.reply_data)
        expected_str = reply.body + "     (posted at " + str(reply.created_at) + ")"
        self.assertEqual(str(reply), expected_str)

    def test_reply_auto_timestamps(self):
        """Test that created_at is automatically set"""
        reply = Reply.objects.create(**self.reply_data)
        self.assertIsNotNone(reply.created_at)
        self.assertIsInstance(reply.created_at, datetime)
