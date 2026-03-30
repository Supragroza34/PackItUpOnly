from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.test import TestCase
from KCLTicketingSystems.models import Ticket, User
from rest_framework_simplejwt.tokens import RefreshToken

class AdminViewsAPIEdgeCasesTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="adminpass123",
            k_number="99999999",
            role=User.Role.ADMIN,
            is_superuser=True,
        )
        self.student = User.objects.create_user(
            username="student",
            email="student@test.com",
            password="studentpass123",
            k_number="11111111",
            role=User.Role.STUDENT,
        )
        self.ticket = Ticket.objects.create(
            user=self.student,
            department="Informatics",
            type_of_issue="Test Issue",
            additional_details="Test details",
        )
        self._auth(self.admin)

    def _auth(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_dashboard_stats_exception(self):
        # Patch auto_close_stale_awaiting_response to raise
        from unittest.mock import patch
        with patch("KCLTicketingSystems.views.admin_views.auto_close_stale_awaiting_response", side_effect=Exception("fail")):
            resp = self.client.get("/api/admin/dashboard/stats/")
            self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn("error", resp.data)

    def test_admin_ticket_detail_not_found(self):
        resp = self.client.get(f"/api/admin/tickets/99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", resp.data)

    def test_admin_ticket_update_not_found(self):
        resp = self.client.patch(f"/api/admin/tickets/99999/update/", {"status": "closed"})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", resp.data)

    def test_admin_ticket_update_invalid_data(self):
        resp = self.client.patch(f"/api/admin/tickets/{self.ticket.id}/update/", {"status": "not_a_status"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_ticket_delete_not_found(self):
        resp = self.client.delete(f"/api/admin/tickets/99999/delete/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", resp.data)

    def test_admin_user_detail_not_found(self):
        resp = self.client.get(f"/api/admin/users/99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", resp.data)

    def test_admin_user_update_not_found(self):
        resp = self.client.patch(f"/api/admin/users/99999/update/", {"role": "staff"})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", resp.data)

    def test_admin_user_update_invalid_data(self):
        resp = self.client.patch(f"/api/admin/users/{self.student.id}/update/", {"role": "not_a_role"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)  # role is not validated strictly

    def test_admin_user_delete_not_found(self):
        resp = self.client.delete(f"/api/admin/users/99999/delete/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", resp.data)

    def test_admin_ticket_update_exception(self):
        from unittest.mock import patch
        with patch("KCLTicketingSystems.views.admin_views.Ticket.objects.select_related", side_effect=Exception("fail")):
            resp = self.client.patch(f"/api/admin/tickets/{self.ticket.id}/update/", {"status": "closed"})
            self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn("error", resp.data)

    def test_admin_ticket_delete_exception(self):
        from unittest.mock import patch
        with patch("KCLTicketingSystems.views.admin_views.Ticket.objects.get", side_effect=Exception("fail")):
            resp = self.client.delete(f"/api/admin/tickets/{self.ticket.id}/delete/")
            self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn("error", resp.data)

    def test_admin_user_update_exception(self):
        from unittest.mock import patch
        self.client.force_authenticate(user=self.admin)
        with patch("KCLTicketingSystems.views.admin_views.User.objects.get", side_effect=Exception("fail")):
            resp = self.client.patch(f"/api/admin/users/{self.student.id}/update/", {"role": "staff"})
            self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn("error", resp.data)
