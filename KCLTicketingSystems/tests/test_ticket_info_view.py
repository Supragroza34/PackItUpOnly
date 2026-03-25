from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from KCLTicketingSystems.models import Ticket, User


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
    
    def test_ticket_info_allows_admin_role(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"/api/staff/dashboard/{self.ticket.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ticket_info_returns_404_for_nonexistent_ticket(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.get("/api/staff/dashboard/99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_ticket_info_superuser_can_access(self):
        superuser = User.objects.create_superuser(
            username="superuser_info",
            email="superuser@test.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=superuser)
        response = self.client.get(f"/api/staff/dashboard/{self.ticket.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_closed_by_role_returns_none_when_ticket_not_closed(self):
        self.client.force_authenticate(user=self.staff)
        pending_ticket = Ticket.objects.get(type_of_issue="Email")
        response = self.client.get(f"/api/staff/dashboard/{pending_ticket.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["closed_by_role"])

    def test_closed_by_role_returns_none_when_closed_by_is_null(self):
        ticket_no_closer = Ticket.objects.create(
            user=self.student,
            assigned_to=self.staff,
            department="Informatics",
            type_of_issue="Printer",
            additional_details="Jammed",
            status=Ticket.Status.CLOSED,
            closed_by=None,
        )
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(f"/api/staff/dashboard/{ticket_no_closer.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["closed_by_role"])

    def test_closed_by_role_lowercased(self):
        """Covers the .lower() call and role fallback branch."""
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(f"/api/staff/dashboard/{self.ticket.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["closed_by_role"], "admin")

    def test_closed_by_role_falls_back_to_student_when_role_is_none(self):
        """Covers the `or 'student'` fallback when closed_by.role is None/empty."""
        with patch.object(self.admin.__class__, 'role', new_callable=lambda: property(lambda self: None)):
            self.client.force_authenticate(user=self.staff)
            response = self.client.get(f"/api/staff/dashboard/{self.ticket.id}/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["closed_by_role"], "student")

    def test_is_overdue_true_for_old_pending_ticket(self):
        from django.utils import timezone
        from datetime import timedelta
        old_ticket = Ticket.objects.create(
            user=self.student,
            assigned_to=self.staff,
            department="Informatics",
            type_of_issue="Old Issue",
            additional_details="Very old",
            status=Ticket.Status.PENDING,
        )
        Ticket.objects.filter(id=old_ticket.id).update(
            created_at=timezone.now() - timedelta(days=4)
        )
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(f"/api/staff/dashboard/{old_ticket.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_overdue"])

    def test_is_overdue_false_for_recent_ticket(self):
        self.client.force_authenticate(user=self.staff)
        pending_ticket = Ticket.objects.get(type_of_issue="Email")
        response = self.client.get(f"/api/staff/dashboard/{pending_ticket.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_overdue"])

    def test_is_overdue_false_for_closed_ticket(self):
        """Closed tickets are never overdue regardless of age."""
        from django.utils import timezone
        from datetime import timedelta
        Ticket.objects.filter(id=self.ticket.id).update(
            created_at=timezone.now() - timedelta(days=10)
        )
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(f"/api/staff/dashboard/{self.ticket.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_overdue"])

    def test_staff_ticket_update_requires_authentication(self):
        response = self.client.patch(f"/api/staff/dashboard/{self.ticket.id}/update/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_staff_ticket_update_rejects_student(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.patch(f"/api/staff/dashboard/{self.ticket.id}/update/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_ticket_update_returns_404_for_nonexistent_ticket(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.patch("/api/staff/dashboard/99999/update/", {'status': 'closed'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_staff_ticket_update_forbidden_if_not_assigned(self):
        """Staff cannot update tickets not assigned to them."""
        self.client.force_authenticate(user=self.other_staff)
        pending_ticket = Ticket.objects.get(type_of_issue="Email") 
        response = self.client.patch(
            f"/api/staff/dashboard/{pending_ticket.id}/update/",
            {'status': 'closed'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_ticket_update_valid(self):
        pending_ticket = Ticket.objects.get(type_of_issue="Email")
        self.client.force_authenticate(user=self.staff)
        response = self.client.patch(
            f"/api/staff/dashboard/{pending_ticket.id}/update/",
            {'status': 'closed'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pending_ticket.refresh_from_db()
        self.assertEqual(pending_ticket.closed_by, self.staff)

    def test_staff_ticket_update_invalid_data(self):
        pending_ticket = Ticket.objects.get(type_of_issue="Email")
        self.client.force_authenticate(user=self.staff)
        response = self.client.patch(
            f"/api/staff/dashboard/{pending_ticket.id}/update/",
            {'status': 'invalid_status'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_staff_ticket_update_admin_can_update_any_ticket(self):
        """Admin can update tickets not assigned to them."""
        pending_ticket = Ticket.objects.get(type_of_issue="Email")
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/staff/dashboard/{pending_ticket.id}/update/",
            {'status': 'closed'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_staff_ticket_update_does_not_set_closed_by_if_not_closed(self):
        in_progress_ticket = Ticket.objects.get(type_of_issue="VPN")
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/staff/dashboard/{in_progress_ticket.id}/update/",
            {'status': 'pending'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        in_progress_ticket.refresh_from_db()
        self.assertIsNone(in_progress_ticket.closed_by)

    def test_staff_ticket_reassign_requires_authentication(self):
        response = self.client.patch(f"/api/staff/dashboard/{self.ticket.id}/reassign/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_staff_ticket_reassign_rejects_student(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.patch(f"/api/staff/dashboard/{self.ticket.id}/reassign/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_ticket_reassign_returns_404_for_nonexistent_ticket(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.patch(
            "/api/staff/dashboard/99999/reassign/",
            {'assigned_to': self.other_staff.id},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_staff_ticket_reassign_valid(self):
        pending_ticket = Ticket.objects.get(type_of_issue="Email")
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/staff/dashboard/{pending_ticket.id}/reassign/",
            {'assigned_to': self.other_staff.id},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pending_ticket.refresh_from_db()
        self.assertEqual(pending_ticket.assigned_to, self.other_staff)

    def test_staff_ticket_reassign_invalid_data(self):
        pending_ticket = Ticket.objects.get(type_of_issue="Email")
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/staff/dashboard/{pending_ticket.id}/reassign/",
            {'assigned_to': 99999},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_staff_ticket_reassign_put_method_works(self):
        pending_ticket = Ticket.objects.get(type_of_issue="Email")
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(
            f"/api/staff/dashboard/{pending_ticket.id}/reassign/",
            {'assigned_to': self.other_staff.id},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)