from django.test import TestCase
from ..models import Reply, Ticket
from datetime import datetime


class ReplyModelTest(TestCase):
    """Test cases for the Reply model"""

    def setUp(self):
        """Set up test data"""

        # create a ticket (as in test_ticket.py)
        self.ticket_data = {
            'name': 'John',
            'surname': 'Doe',
            'k_number': '12345678',
            'k_email': 'K12345678@kcl.ac.uk',
            'department': 'Informatics',
            'type_of_issue': 'Software Installation Issues',
            'additional_details': 'Need help installing Python'
        }
        ticket = Ticket.objects.create(**self.ticket_data)
        body = "Try switching off and then on again."
        self.reply_data = {
            'ticket': ticket,
            'body': body,
        }

    def test_reply_creation(self):
        """Test creating a reply"""
        reply = Reply.objects.create(**self.reply_data)
        self.assertEqual(reply.body, 'Try switching off and then on again.')
        self.assertEqual(reply.ticket.name, 'John')
        self.assertEqual(reply.ticket.surname, 'Doe')
        self.assertEqual(reply.ticket.k_number, '12345678')
        self.assertEqual(reply.ticket.k_email, 'K12345678@kcl.ac.uk')
        self.assertEqual(reply.ticket.department, 'Informatics')
        self.assertEqual(reply.ticket.type_of_issue, 'Software Installation Issues')
        self.assertEqual(reply.ticket.additional_details, 'Need help installing Python')
        self.assertIsNotNone(reply.ticket.created_at)
        self.assertIsNotNone(reply.ticket.updated_at)

    def test_reply_str_method(self):
        """Test the __str__ method of Reply model"""
        reply = Reply.objects.create(**self.reply_data)
        expected_str = reply.body + "     (posted at " + reply.created_at + ")"
        self.assertEqual(str(reply), expected_str)

    def test_reply_auto_timestamps(self):
        """Test that created_at is automatically set"""
        reply = Reply.objects.create(**self.reply_data)
        self.assertIsNotNone(reply.created_at)
        self.assertIsInstance(reply.created_at, datetime)
