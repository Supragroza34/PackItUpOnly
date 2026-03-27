from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from KCLTicketingSystems.models import Attachment, Ticket, User
from KCLTicketingSystems.views.ticket_info_view import AttachmentSerializer, _staff_can_access_ticket


class TicketInfoAndStaffListViewTests(APITestCase):
    STAFF_LIST_URL = "/api/staff/list/"

    def setUp(self):
        self._create_users()
        self._create_primary_ticket_and_attachment()
        self._create_extra_tickets()

    def _create_users(self):
        users = {
            "student": ("student_info", "student_info@test.com", User.Role.STUDENT, "81001001", "Stu", "Dent", "Informatics"),
            "staff": ("staff_info", "staff_info@test.com", User.Role.STAFF, "81001002", "Sam", "Staff", "Informatics"),
            "other_staff": ("staff_other_info", "staff_other_info@test.com", User.Role.STAFF, "81001003", "Olive", "Other", "Informatics"),
            "admin": ("admin_info", "admin_info@test.com", User.Role.ADMIN, "81001004", "Ada", "Min", "Informatics"),
            "staff_other_department": ("staff_math_info", "staff_math_info@test.com", User.Role.STAFF, "81001005", "Mia", "Math", "Maths"),
        }
        for attr, args in users.items():
            setattr(self, attr, self._create_user(*args))

    def _create_user(self, username, email, role, k_number, first_name, last_name, department):
        return User.objects.create_user(
            username=username,
            email=email,
            password="testpass123",
            role=role,
            department=department,
            k_number=k_number,
            first_name=first_name,
            last_name=last_name,
        )

    def _create_primary_ticket_and_attachment(self):
        self.ticket = Ticket.objects.create(
            user=self.student,
            assigned_to=self.staff,
            department="Informatics",
            type_of_issue="WiFi",
            additional_details="Drops often",
            status=Ticket.Status.CLOSED,
            closed_by=self.admin,
            priority=Ticket.Priority.HIGH,
        )
        self.attachment = self._create_attachment(self.ticket)

    def _create_attachment(self, ticket):
        return Attachment.objects.create(
            ticket=ticket,
            file=SimpleUploadedFile(
                "evidence.txt",
                b"connection drops every 30 minutes",
                content_type="text/plain",
            ),
            original_filename="evidence.txt",
        )

    def _create_extra_tickets(self):
        Ticket.objects.create(
            user=self.student,
            assigned_to=self.staff,
            department="Informatics",
            type_of_issue="Email",
            additional_details="Inbox unavailable",
            status=Ticket.Status.PENDING,
        )

        Ticket.objects.create(
            user=self.student,
            assigned_to=self.other_staff,
            department="Informatics",
            type_of_issue="VPN",
            additional_details="Cannot connect",
            status=Ticket.Status.IN_PROGRESS,
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def _ticket_info_url(self, ticket_id=None):
        return f"/api/staff/dashboard/{ticket_id or self.ticket.id}/"

    def _reassign_url(self, ticket_id=None):
        return f"{self._ticket_info_url(ticket_id)}reassign/"

    def _update_url(self, ticket_id=None):
        return f"{self._ticket_info_url(ticket_id)}update/"

    def test_ticket_info_requires_authentication(self):
        response = self.client.get(self._ticket_info_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ticket_info_rejects_student_role(self):
        self._auth(self.student)
        response = self.client.get(self._ticket_info_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_ticket_info_returns_closed_by_role_for_staff_view(self):
        self._auth(self.staff)
        response = self.client.get(self._ticket_info_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.ticket.id)
        self.assertEqual(response.data["status"], "closed")
        self.assertEqual(response.data["closed_by_role"], "admin")
        self.assertEqual(response.data["user"]["first_name"], "Stu")

    def test_ticket_info_includes_attachment_metadata_and_url(self):
        self._auth(self.staff)
        response = self.client.get(self._ticket_info_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("attachments", response.data)
        self.assertEqual(len(response.data["attachments"]), 1)

        attachment_data = response.data["attachments"][0]
        self.assertEqual(attachment_data["original_filename"], "evidence.txt")
        self.assertTrue(attachment_data["file_size"] > 0)
        self.assertIn("/media/attachments/", attachment_data["file_url"])

    def test_ticket_info_open_ticket_has_null_closed_by_role(self):
        open_ticket = Ticket.objects.create(
            user=self.student,
            assigned_to=self.staff,
            department="Informatics",
            type_of_issue="Printer",
            additional_details="Paper jam",
            status=Ticket.Status.PENDING,
        )
        self._auth(self.staff)
        response = self.client.get(self._ticket_info_url(open_ticket.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["closed_by_role"])

    def test_attachment_serializer_returns_relative_url_without_request(self):
        serializer = AttachmentSerializer(self.attachment)
        self.assertTrue(serializer.data["file_url"].startswith("/media/"))

    def test_attachment_serializer_returns_none_when_file_missing(self):
        attachment = Attachment(
            ticket=self.ticket,
            original_filename="missing.txt",
            file_size=0,
        )
        serializer = AttachmentSerializer(attachment)
        self.assertIsNone(serializer.data["file_url"])

    def test_department_staff_list_requires_authentication(self):
        response = self.client.get(self.STAFF_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_department_staff_list_returns_same_department_staff_and_admin(self):
        self._auth(self.staff)
        response = self.client.get(self.STAFF_LIST_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        staff_ids = [item["id"] for item in response.data["staff"]]

        self.assertIn(self.staff.id, staff_ids)
        self.assertIn(self.other_staff.id, staff_ids)
        self.assertIn(self.admin.id, staff_ids)
        self.assertNotIn(self.staff_other_department.id, staff_ids)
        self.assertNotIn(self.student.id, staff_ids)

    def test_department_staff_list_includes_open_ticket_count_only(self):
        self._auth(self.staff)
        response = self.client.get(self.STAFF_LIST_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        by_id = {item["id"]: item for item in response.data["staff"]}

        # self.staff has one pending (open) and one closed (excluded from count)
        self.assertEqual(by_id[self.staff.id]["ticket_count"], 1)
        # self.other_staff has one in_progress (open)
        self.assertEqual(by_id[self.other_staff.id]["ticket_count"], 1)
        # admin has no assigned open tickets
        self.assertEqual(by_id[self.admin.id]["ticket_count"], 0)

    def test_department_staff_list_returns_500_on_unexpected_error(self):
        self._auth(self.staff)
        with patch("KCLTicketingSystems.views.ticket_info_view.User.objects.filter", side_effect=Exception("boom")):
            response = self.client.get(self.STAFF_LIST_URL)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["error"], "boom")

    def test_unauthenticated_user_cannot_reassign_ticket(self):
        response = self.client.patch(self._reassign_url(), {
            "assigned_to": self.other_staff.id
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_cannot_reassign_ticket(self):
        self._auth(self.student)

        response = self.client.patch(self._reassign_url(), {
            "assigned_to": self.other_staff.id
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_ticket_reassigns_correctly(self):
        self._auth(self.staff)

        response = self.client.patch(self._reassign_url(), {
            "assigned_to": self.other_staff.id
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.assigned_to, self.other_staff)

    def test_invalid_patch_returns_400_error(self):
        self._auth(self.staff)

        response = self.client.patch(self._reassign_url(), {
            "assigned_to": "not_valid_data"
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_existent_ticket_cannot_be_reassigned(self):
        self._auth(self.staff)

        response = self.client.patch(self._reassign_url(9999999999999999), {
            "assigned_to": self.other_staff.id
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_reassign_returns_500_on_unexpected_error(self):
        self._auth(self.staff)
        with patch("KCLTicketingSystems.views.ticket_info_view.Ticket.objects.get", side_effect=Exception("boom")):
            response = self.client.patch(
                self._reassign_url(),
                {"assigned_to": self.other_staff.id},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["error"], "boom")

    def test_staff_can_access_ticket_helper_for_admin(self):
        self.assertTrue(_staff_can_access_ticket(self.admin, self.ticket))

    def test_staff_ticket_update_requires_authentication(self):
        response = self.client.patch(
            self._update_url(),
            {"status": Ticket.Status.CLOSED},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_staff_ticket_update_rejects_student(self):
        self._auth(self.student)
        response = self.client.patch(
            self._update_url(),
            {"status": Ticket.Status.CLOSED},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_ticket_update_rejects_unassigned_staff(self):
        self._auth(self.other_staff)
        response = self.client.patch(
            self._update_url(),
            {"status": Ticket.Status.CLOSED},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"], "Access denied")

    def test_staff_ticket_update_returns_400_for_invalid_status(self):
        self._auth(self.staff)
        response = self.client.patch(
            self._update_url(),
            {"status": "invalid_status"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_staff_ticket_update_closes_ticket_and_sets_closed_by(self):
        open_ticket = Ticket.objects.create(
            user=self.student,
            assigned_to=self.staff,
            department="Informatics",
            type_of_issue="MFA",
            additional_details="Token expired",
            status=Ticket.Status.PENDING,
        )
        self._auth(self.staff)

        response = self.client.patch(
            self._update_url(open_ticket.id),
            {"status": Ticket.Status.CLOSED},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        open_ticket.refresh_from_db()
        self.assertEqual(open_ticket.status, Ticket.Status.CLOSED)
        self.assertEqual(open_ticket.closed_by, self.staff)
