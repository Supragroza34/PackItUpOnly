from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from KCLTicketingSystems.models import Attachment, Ticket, User
from KCLTicketingSystems.views.ticket_info_view import AttachmentSerializer, _staff_can_access_ticket


class TicketInfoAndStaffListViewTests(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="student_info",
            email="student_info@test.com",
            password="testpass123",
            role=User.Role.STUDENT,
            department="Informatics",
            k_number="81001001",
            first_name="Stu",
            last_name="Dent",
        )
        self.staff = User.objects.create_user(
            username="staff_info",
            email="staff_info@test.com",
            password="testpass123",
            role=User.Role.STAFF,
            department="Informatics",
            k_number="81001002",
            first_name="Sam",
            last_name="Staff",
        )
        self.other_staff = User.objects.create_user(
            username="staff_other_info",
            email="staff_other_info@test.com",
            password="testpass123",
            role=User.Role.STAFF,
            department="Informatics",
            k_number="81001003",
            first_name="Olive",
            last_name="Other",
        )
        self.admin = User.objects.create_user(
            username="admin_info",
            email="admin_info@test.com",
            password="testpass123",
            role=User.Role.ADMIN,
            department="Informatics",
            k_number="81001004",
            first_name="Ada",
            last_name="Min",
        )
        self.staff_other_department = User.objects.create_user(
            username="staff_math_info",
            email="staff_math_info@test.com",
            password="testpass123",
            role=User.Role.STAFF,
            department="Maths",
            k_number="81001005",
            first_name="Mia",
            last_name="Math",
        )

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

        self.attachment = Attachment.objects.create(
            ticket=self.ticket,
            file=SimpleUploadedFile(
                "evidence.txt",
                b"connection drops every 30 minutes",
                content_type="text/plain",
            ),
            original_filename="evidence.txt",
        )

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

    def test_ticket_info_requires_authentication(self):
        response = self.client.get(f"/api/staff/dashboard/{self.ticket.id}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ticket_info_rejects_student_role(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(f"/api/staff/dashboard/{self.ticket.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_ticket_info_returns_closed_by_role_for_staff_view(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(f"/api/staff/dashboard/{self.ticket.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.ticket.id)
        self.assertEqual(response.data["status"], "closed")
        self.assertEqual(response.data["closed_by_role"], "admin")
        self.assertEqual(response.data["user"]["first_name"], "Stu")

    def test_ticket_info_includes_attachment_metadata_and_url(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(f"/api/staff/dashboard/{self.ticket.id}/")

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
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(f"/api/staff/dashboard/{open_ticket.id}/")

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
        response = self.client.get("/api/staff/list/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_department_staff_list_returns_same_department_staff_and_admin(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.get("/api/staff/list/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        staff_ids = [item["id"] for item in response.data["staff"]]

        self.assertIn(self.staff.id, staff_ids)
        self.assertIn(self.other_staff.id, staff_ids)
        self.assertIn(self.admin.id, staff_ids)
        self.assertNotIn(self.staff_other_department.id, staff_ids)
        self.assertNotIn(self.student.id, staff_ids)

    def test_department_staff_list_includes_open_ticket_count_only(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.get("/api/staff/list/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        by_id = {item["id"]: item for item in response.data["staff"]}

        # self.staff has one pending (open) and one closed (excluded from count)
        self.assertEqual(by_id[self.staff.id]["ticket_count"], 1)
        # self.other_staff has one in_progress (open)
        self.assertEqual(by_id[self.other_staff.id]["ticket_count"], 1)
        # admin has no assigned open tickets
        self.assertEqual(by_id[self.admin.id]["ticket_count"], 0)

    def test_department_staff_list_returns_500_on_unexpected_error(self):
        self.client.force_authenticate(user=self.staff)
        with patch("KCLTicketingSystems.views.ticket_info_view.User.objects.filter", side_effect=Exception("boom")):
            response = self.client.get("/api/staff/list/")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["error"], "boom")

    def test_unauthenticated_user_cannot_reassign_ticket(self):
        response = self.client.patch(f"/api/staff/dashboard/{self.ticket.id}/reassign/", {
            "assigned_to": self.other_staff.id
        }, format='json')        

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_cannot_reassign_ticket(self):
        self.client.force_authenticate(user=self.student)

        response = self.client.patch(f"/api/staff/dashboard/{self.ticket.id}/reassign/", {
            "assigned_to": self.other_staff.id
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_ticket_reassigns_correctly(self):
        self.client.force_authenticate(user=self.staff)

        response = self.client.patch(f"/api/staff/dashboard/{self.ticket.id}/reassign/", {
            "assigned_to": self.other_staff.id
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.assigned_to, self.other_staff)

    def test_invalid_patch_returns_400_error(self):
        self.client.force_authenticate(user=self.staff)

        response = self.client.patch(f"/api/staff/dashboard/{self.ticket.id}/reassign/", {
            "assigned_to": "not_valid_data"
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_existent_ticket_cannot_be_reassigned(self):
        self.client.force_authenticate(user=self.staff)

        response = self.client.patch(f"/api/staff/dashboard/9999999999999999/reassign/", {
            "assigned_to": self.other_staff.id
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_reassign_returns_500_on_unexpected_error(self):
        self.client.force_authenticate(user=self.staff)
        with patch("KCLTicketingSystems.views.ticket_info_view.Ticket.objects.get", side_effect=Exception("boom")):
            response = self.client.patch(
                f"/api/staff/dashboard/{self.ticket.id}/reassign/",
                {"assigned_to": self.other_staff.id},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["error"], "boom")

    def test_staff_can_access_ticket_helper_for_admin(self):
        self.assertTrue(_staff_can_access_ticket(self.admin, self.ticket))

    def test_staff_ticket_update_requires_authentication(self):
        response = self.client.patch(
            f"/api/staff/dashboard/{self.ticket.id}/update/",
            {"status": Ticket.Status.CLOSED},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_staff_ticket_update_rejects_student(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.patch(
            f"/api/staff/dashboard/{self.ticket.id}/update/",
            {"status": Ticket.Status.CLOSED},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_ticket_update_rejects_unassigned_staff(self):
        self.client.force_authenticate(user=self.other_staff)
        response = self.client.patch(
            f"/api/staff/dashboard/{self.ticket.id}/update/",
            {"status": Ticket.Status.CLOSED},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"], "Access denied")

    def test_staff_ticket_update_returns_400_for_invalid_status(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.patch(
            f"/api/staff/dashboard/{self.ticket.id}/update/",
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
        self.client.force_authenticate(user=self.staff)

        response = self.client.patch(
            f"/api/staff/dashboard/{open_ticket.id}/update/",
            {"status": Ticket.Status.CLOSED},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        open_ticket.refresh_from_db()
        self.assertEqual(open_ticket.status, Ticket.Status.CLOSED)
        self.assertEqual(open_ticket.closed_by, self.staff)
       