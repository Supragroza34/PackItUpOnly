from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch

from ..models import Ticket


class EmailWebhookTest(TestCase):
    """
    Tests for the email webhook endpoint that creates tickets from incoming emails.
    """

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/email-webhook/"

        # Example payload similar to what Mailgun sends
        self.mailgun_payload = {
            "from": "K23163890@kcl.ac.uk",
            "subject": "Computer not turning on",
            "text": (
                "Hello,\n\n"
                "My name is Amey Tripathi.\n"
                "K-Number: K23163890\n"
                "Department: Informatics\n"
                "The computer in lab 3 will not power on.\n"
            ),
        }

    @patch("KCLTicketingSystems.views.email_webhook.extract_ticket_info_with_ai")
    def test_webhook_creates_ticket_from_email(self, mock_extract):
        """
        When the webhook receives a valid email payload and AI extraction succeeds,
        it should create a Ticket and return a 200 response with ticket_id.
        """
        mock_extract.return_value = {
            "name": "Amey",
            "surname": "Tripathi",
            "k_number": "23163890",
            "k_email": "K23163890@kcl.ac.uk",
            "department": "Informatics",
            "type_of_issue": "Computer not turning on",
            "additional_details": "The computer in lab 3 will not power on.",
        }

        response = self.client.post(self.url, self.mailgun_payload, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertIn("ticket_id", response.data)
        self.assertEqual(response.data["message"], "Ticket created successfully")

        ticket_id = response.data["ticket_id"]
        ticket = Ticket.objects.get(id=ticket_id)
        self.assertEqual(ticket.name, "Amey")
        self.assertEqual(ticket.surname, "Tripathi")
        self.assertEqual(ticket.k_number, "23163890")
        self.assertEqual(ticket.k_email, "K23163890@kcl.ac.uk")
        self.assertEqual(ticket.department, "Informatics")
        self.assertEqual(ticket.type_of_issue, "Computer not turning on")

    @patch("KCLTicketingSystems.views.email_webhook.extract_ticket_info_with_ai")
    def test_webhook_allows_multiple_tickets_same_k_number(self, mock_extract):
        """
        The same K-Number should be able to generate multiple tickets (no UNIQUE constraint).
        """
        mock_extract.return_value = {
            "name": "Amey",
            "surname": "Tripathi",
            "k_number": "23163890",
            "k_email": "K23163890@kcl.ac.uk",
            "department": "Informatics",
            "type_of_issue": "Issue 1",
            "additional_details": "First issue details",
        }

        # First ticket
        resp1 = self.client.post(self.url, self.mailgun_payload, format="multipart")
        self.assertEqual(resp1.status_code, status.HTTP_200_OK)

        # Change subject / details to simulate a different email, same K-number
        second_payload = self.mailgun_payload.copy()
        second_payload["subject"] = "Different issue"
        mock_extract.return_value["type_of_issue"] = "Issue 2"
        mock_extract.return_value["additional_details"] = "Second issue details"

        resp2 = self.client.post(self.url, second_payload, format="multipart")
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)

        # Verify two tickets exist for same K-number
        tickets = Ticket.objects.filter(k_number="23163890")
        self.assertEqual(tickets.count(), 2)

