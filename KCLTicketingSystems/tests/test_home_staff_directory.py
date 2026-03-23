"""Tests for SPA home views, staff directory API, staff meeting detail, and department staff list."""
from unittest.mock import mock_open, patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class HomeAndSpaViewTests(TestCase):
    """home() and spa_catchall() serve React build or fallback template."""

    @patch("KCLTicketingSystems.views.home_view.FRONTEND_INDEX")
    def test_home_uses_fallback_template_when_no_build(self, mock_index):
        """Force exists() False so we hit render() even if repo has frontend/build locally."""
        mock_index.exists.return_value = False
        client = Client()
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"KCL Ticketing System", response.content)

    @patch("KCLTicketingSystems.views.home_view.FRONTEND_INDEX")
    def test_spa_catchall_uses_fallback_when_no_build(self, mock_index):
        mock_index.exists.return_value = False
        client = Client()
        response = client.get("/login/sub")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"KCL Ticketing System", response.content)

    @patch("builtins.open", new_callable=mock_open, read_data="<!DOCTYPE html><title>ReactBuild</title>")
    @patch("KCLTicketingSystems.views.home_view.FRONTEND_INDEX")
    def test_home_serves_built_index_when_present(self, mock_index, _mock_file):
        mock_index.exists.return_value = True

        client = Client()
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ReactBuild", response.content)

    @patch("builtins.open", new_callable=mock_open, read_data="<html>SPA</html>")
    @patch("KCLTicketingSystems.views.home_view.FRONTEND_INDEX")
    def test_spa_catchall_serves_same_build(self, mock_index, _mock_file):
        mock_index.exists.return_value = True

        client = Client()
        response = client.get("/dashboard/foo")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"SPA", response.content)


class StaffDirectoryAPITests(TestCase):
    """GET /api/staff/ — staff directory for authenticated users."""

    def setUp(self):
        self.client = APIClient()
        self.student = User.objects.create_user(
            username="student_sd",
            email="student_sd@example.com",
            password="pass12345",
            role=User.Role.STUDENT,
            department="IT",
        )
        self.staff_it = User.objects.create_user(
            username="staff_it",
            email="staff_it@example.com",
            password="pass12345",
            role=User.Role.STAFF,
            department="IT",
            first_name="Alice",
            last_name="Adams",
        )
        self.staff_hr = User.objects.create_user(
            username="staff_hr",
            email="staff_hr@example.com",
            password="pass12345",
            role=User.Role.STAFF,
            department="HR",
            first_name="Bob",
            last_name="Brown",
        )

    def test_staff_directory_requires_auth(self):
        r = self.client.get("/api/staff/")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_staff_directory_lists_staff_ordered(self):
        self.client.force_authenticate(user=self.student)
        r = self.client.get("/api/staff/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        data = r.json()
        self.assertIsInstance(data, list)
        emails = {row["email"] for row in data}
        self.assertIn("staff_it@example.com", emails)
        self.assertIn("staff_hr@example.com", emails)

    def test_staff_directory_filter_by_department(self):
        self.client.force_authenticate(user=self.student)
        r = self.client.get("/api/staff/", {"department": "it"})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        depts = {row["department"] for row in r.json()}
        self.assertEqual(depts, {"IT"})


class StaffMeetingDetailTests(TestCase):
    """GET /api/staff/<id>/ — staff profile + office hours."""

    def setUp(self):
        self.client = APIClient()
        self.student = User.objects.create_user(
            username="stu_sm",
            email="stu_sm@example.com",
            password="pass12345",
            role=User.Role.STUDENT,
        )
        self.staff_user = User.objects.create_user(
            username="staff_sm",
            email="staff_sm@example.com",
            password="pass12345",
            role=User.Role.STAFF,
            department="IT",
        )

    def test_staff_meeting_requires_auth(self):
        r = self.client.get(f"/api/staff/{self.staff_user.id}/")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_staff_meeting_returns_staff_serializer(self):
        self.client.force_authenticate(user=self.student)
        r = self.client.get(f"/api/staff/{self.staff_user.id}/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json()["id"], self.staff_user.id)
        self.assertEqual(r.json()["email"], "staff_sm@example.com")

    def test_staff_meeting_404_for_non_staff_user_id(self):
        self.client.force_authenticate(user=self.student)
        r = self.client.get(f"/api/staff/{self.student.id}/")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)


class DepartmentStaffListTests(TestCase):
    """GET /api/staff/list/ — colleagues in same department for reassignment."""

    def setUp(self):
        self.client = APIClient()
        self.staff_it = User.objects.create_user(
            username="ds_staff1",
            email="ds_staff1@example.com",
            password="pass12345",
            role=User.Role.STAFF,
            department="Finance",
        )
        self.staff_it2 = User.objects.create_user(
            username="ds_staff2",
            email="ds_staff2@example.com",
            password="pass12345",
            role=User.Role.STAFF,
            department="Finance",
        )
        self.admin_fin = User.objects.create_user(
            username="ds_admin",
            email="ds_admin@example.com",
            password="pass12345",
            role=User.Role.ADMIN,
            department="Finance",
        )

    def test_department_staff_list_requires_auth(self):
        r = self.client.get("/api/staff/list/")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_department_staff_list_returns_same_department_staff_and_admin(self):
        self.client.force_authenticate(user=self.staff_it)
        r = self.client.get("/api/staff/list/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        body = r.json()
        self.assertIn("staff", body)
        ids = {row["id"] for row in body["staff"]}
        self.assertIn(self.staff_it.id, ids)
        self.assertIn(self.staff_it2.id, ids)
        self.assertIn(self.admin_fin.id, ids)
