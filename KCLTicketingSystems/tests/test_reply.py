from django.test import TestCase
from datetime import datetime
from KCLTicketingSystems.models import Ticket, Reply, User


class ReplyModelTest(TestCase):
    """Test cases for the Reply model"""

    STUDENT_EMAIL = "teststudent@test.com"
    REPLY_BODY = "Try switching off and then on again."

    def setUp(self):
        """Set up test data"""
        self.student = self._create_student()
        self.staff = self._create_staff()
        self.ticket_data = self._build_ticket_data()
        ticket = Ticket.objects.create(**self.ticket_data)
        self.reply_data = self._build_reply_data(ticket)

    def _create_student(self):
        return User.objects.create_user(
            username="teststudent",
            email=self.STUDENT_EMAIL,
            password="testpass123",
            first_name="Tester",
            last_name="One",
            k_number="73573402",
            role=User.Role.STUDENT,
        )

    def _create_staff(self):
        return User.objects.create_user(
            username="teststaff",
            email="teststaff@test.com",
            password="testpass123",
            first_name="Tester",
            last_name="Two",
            k_number="73573473",
            role=User.Role.STAFF,
        )

    def _build_ticket_data(self):
        return {
            "user": self.student,
            "department": "Informatics",
            "type_of_issue": "Software Installation Issues",
            "additional_details": "Need help installing Python",
        }

    def _build_reply_data(self, ticket):
        return {
            "user": self.staff,
            "ticket": ticket,
            "body": self.REPLY_BODY,
        }

    def test_reply_creation(self):
        """Test creating a reply"""
        reply = Reply.objects.create(**self.reply_data)
        self.assertEqual(reply.user.role, "staff")
        self.assertEqual(reply.body, self.REPLY_BODY)
        self.assertEqual(reply.ticket.user.first_name, "Tester")
        self.assertEqual(reply.ticket.user.last_name, "One")
        self.assertEqual(reply.ticket.user.k_number, "73573402")
        self.assertEqual(reply.ticket.user.email, self.STUDENT_EMAIL)
        self.assertEqual(reply.ticket.department, "Informatics")
        self.assertEqual(reply.ticket.type_of_issue, "Software Installation Issues")
        self.assertEqual(reply.ticket.additional_details, "Need help installing Python")
        self.assertIsNotNone(reply.ticket.created_at)
        self.assertIsNotNone(reply.ticket.updated_at)

    def test_reply_str_method(self):
        """Test the __str__ method of Reply model"""
        reply = Reply.objects.create(**self.reply_data)
        expected_str = reply.body + " (posted at " + str(reply.created_at) + ")"
        self.assertEqual(str(reply), expected_str)

    def test_reply_auto_timestamps(self):
        """Test that created_at is automatically set"""
        reply = Reply.objects.create(**self.reply_data)
        self.assertIsNotNone(reply.created_at)
        self.assertIsInstance(reply.created_at, datetime)
