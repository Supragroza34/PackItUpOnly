from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from ..models import Attachment, Ticket
from ..models.user import User
from ..sanitizer import sanitize_additional_details
from ..serializers import TicketCreateSerializer


class RichTextSanitizerTests(TestCase):
    """Group rich text ticket feature checks so the user workflow is guarded against regressions."""
    def test_sanitize_returns_empty_for_none_and_empty(self):
        """Guard sanitize returns empty for none and empty in the rich text ticket feature flow so regressions surface early."""
        self.assertEqual(sanitize_additional_details(None), "")
        self.assertEqual(sanitize_additional_details(""), "")

    def test_sanitize_keeps_only_supported_formatting(self):
        """Guard sanitize keeps only supported formatting in the rich text ticket feature flow so regressions surface early."""
        html = (
            '<p data-indent="2" style="color:red">'
            'Hello <strong>Bold</strong> <em>Italic</em> '
            '<u>Underline</u><script>alert(1)</script></p>'
            '<ol><li>One</li></ol>'
        )

        cleaned = sanitize_additional_details(html)

        self.assertIn('<p data-indent="2">', cleaned)
        self.assertIn("<strong>Bold</strong>", cleaned)
        self.assertIn("<em>Italic</em>", cleaned)
        self.assertIn("<ol><li>One</li></ol>", cleaned)
        self.assertNotIn("style=", cleaned)
        self.assertNotIn("<u>", cleaned)
        self.assertNotIn("<script", cleaned)


class TicketCreateSerializerRichTextTests(TestCase):
    """Group rich text ticket feature checks so the user workflow is guarded against regressions."""
    def setUp(self):
        """Establish shared fixtures so tests stay focused on behavior rather than setup details."""
        self.student = User.objects.create_user(
            username="student1",
            email="student1@test.com",
            password="pass12345",
            k_number="K10000001",
            role=User.Role.STUDENT,
        )
        self.staff_a = User.objects.create_user(
            username="staff_a",
            email="staff_a@test.com",
            password="pass12345",
            k_number="K20000001",
            role=User.Role.STAFF,
            department="Informatics",
        )
        self.staff_b = User.objects.create_user(
            username="staff_b",
            email="staff_b@test.com",
            password="pass12345",
            k_number="K20000002",
            role=User.Role.STAFF,
            department="Informatics",
        )

        Ticket.objects.create(
            user=self.student,
            department="Informatics",
            type_of_issue="Software Installation Issues",
            additional_details="already assigned",
            assigned_to=self.staff_a,
        )

    def test_serializer_assigns_least_loaded_staff_and_sanitizes_details(self):
        """Guard serializer assigns least loaded staff and sanitizes details in the rich text ticket feature flow so regressions surface early."""
        serializer = TicketCreateSerializer()

        ticket = serializer.create(
            {
                "user": self.student,
                "department": "Informatics",
                "type_of_issue": "Software Installation Issues",
                "additional_details": '<p><strong>Safe</strong><img src="x" /></p>',
                "priority": Ticket.Priority.MEDIUM,
            }
        )

        self.assertEqual(ticket.assigned_to, self.staff_b)
        self.assertIn("<strong>Safe</strong>", ticket.additional_details)
        self.assertNotIn("<img", ticket.additional_details)

    def test_serializer_skips_sanitizer_for_empty_details(self):
        """Guard serializer skips sanitizer for empty details in the rich text ticket feature flow so regressions surface early."""
        serializer = TicketCreateSerializer()

        with patch("KCLTicketingSystems.serializers.sanitize_additional_details") as sanitize_mock:
            ticket = serializer.create(
                {
                    "user": self.student,
                    "department": "Informatics",
                    "type_of_issue": "Software Installation Issues",
                    "additional_details": "",
                    "priority": Ticket.Priority.MEDIUM,
                }
            )

        sanitize_mock.assert_not_called()
        self.assertEqual(ticket.additional_details, "")


class TicketCreateViewRichTextAndAttachmentsTests(TestCase):
    """Group rich text ticket feature checks so the user workflow is guarded against regressions."""
    def setUp(self):
        """Establish shared fixtures so tests stay focused on behavior rather than setup details."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="api_student",
            email="api_student@test.com",
            password="pass12345",
            k_number="K30000001",
            role=User.Role.STUDENT,
            department="Informatics",
        )
        self.staff = User.objects.create_user(
            username="api_staff",
            email="api_staff@test.com",
            password="pass12345",
            k_number="K30000002",
            role=User.Role.STAFF,
            department="Informatics",
        )
        self.client.force_authenticate(user=self.user)
        self.url = "/api/tickets/"

    @patch("KCLTicketingSystems.views.ticket_create_view.notify_admin_on_ticket")
    def test_create_ticket_sanitizes_html_and_notifies(self, notify_mock):
        """Guard create ticket sanitizes html and notifies in the rich text ticket feature flow so regressions surface early."""
        payload = {
            "department": "Informatics",
            "type_of_issue": "Software Installation Issues",
            "additional_details": '<p data-indent="1">A <strong>bold</strong> <script>x</script></p>',
            "priority": Ticket.Priority.HIGH,
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, 201)
        ticket = Ticket.objects.get(id=response.data["id"])
        self.assertIn("<strong>bold</strong>", ticket.additional_details)
        self.assertNotIn("<script", ticket.additional_details)
        notify_mock.assert_called_once_with(ticket)

    @patch("KCLTicketingSystems.views.ticket_create_view.notify_admin_on_ticket")
    def test_create_ticket_with_attachments_persists_file_records(self, notify_mock):
        """Guard create ticket with attachments persists file records in the rich text ticket feature flow so regressions surface early."""
        attachment = SimpleUploadedFile(
            "notes.txt",
            b"hello attachment",
            content_type="text/plain",
        )

        response = self.client.post(
            self.url,
            {
                "department": "Informatics",
                "type_of_issue": "Software Installation Issues",
                "additional_details": "<p>hello</p>",
                "priority": Ticket.Priority.MEDIUM,
                "attachments": [attachment],
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        ticket = Ticket.objects.get(id=response.data["id"])
        self.assertEqual(Attachment.objects.filter(ticket=ticket).count(), 1)
        saved_attachment = Attachment.objects.get(ticket=ticket)
        self.assertEqual(saved_attachment.original_filename, "notes.txt")
        self.assertEqual(saved_attachment.file_size, len(b"hello attachment"))
        notify_mock.assert_called_once_with(ticket)
