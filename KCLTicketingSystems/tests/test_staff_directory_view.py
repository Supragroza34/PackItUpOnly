from rest_framework import status
from rest_framework.test import APITestCase

from KCLTicketingSystems.models import User


class StaffDirectoryViewTests(APITestCase):
    """Group staff directory view checks so the user workflow is guarded against regressions."""
    def setUp(self):
        """Establish shared fixtures so tests stay focused on behavior rather than setup details."""
        self.url = "/api/staff/"

        self.student = User.objects.create_user(
            username="student_dir",
            email="student_dir@test.com",
            password="testpass123",
            role=User.Role.STUDENT,
            first_name="Student",
            last_name="User",
            department="Informatics",
            k_number="81000001",
        )

        self.staff_a = User.objects.create_user(
            username="staff_a_dir",
            email="staff_a_dir@test.com",
            password="testpass123",
            role=User.Role.STAFF,
            first_name="Alice",
            last_name="Brown",
            department="informatics",
            k_number="81000002",
        )
        self.staff_b = User.objects.create_user(
            username="staff_b_dir",
            email="staff_b_dir@test.com",
            password="testpass123",
            role=User.Role.STAFF,
            first_name="Bob",
            last_name="Anderson",
            department="Informatics",
            k_number="81000003",
        )
        self.staff_c = User.objects.create_user(
            username="staff_c_dir",
            email="staff_c_dir@test.com",
            password="testpass123",
            role=User.Role.STAFF,
            first_name="Carol",
            last_name="Smith",
            department="Maths",
            k_number="81000004",
        )

    def test_requires_authentication(self):
        """Guard requires authentication in the staff directory view flow so regressions surface early."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_only_staff_users(self):
        """Guard returns only staff users in the staff directory view flow so regressions surface early."""
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = [item["id"] for item in response.data]
        self.assertNotIn(self.student.id, returned_ids)
        self.assertIn(self.staff_a.id, returned_ids)
        self.assertIn(self.staff_b.id, returned_ids)
        self.assertIn(self.staff_c.id, returned_ids)

    def test_department_filter_is_case_insensitive(self):
        """Guard department filter is case insensitive in the staff directory view flow so regressions surface early."""
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.url, {"department": "informatics"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = [item["id"] for item in response.data]
        self.assertIn(self.staff_a.id, returned_ids)
        self.assertIn(self.staff_b.id, returned_ids)
        self.assertNotIn(self.staff_c.id, returned_ids)

    def test_results_are_ordered_by_last_name_then_first_name(self):
        """Guard results are ordered by last name then first name in the staff directory view flow so regressions surface early."""
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ordered_names = [f"{item['last_name']} {item['first_name']}" for item in response.data]
        self.assertEqual(
            ordered_names,
            [
                "Anderson Bob",
                "Brown Alice",
                "Smith Carol",
            ],
        )

    def test_unknown_department_returns_empty_list(self):
        """Guard unknown department returns empty list in the staff directory view flow so regressions surface early."""
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.url, {"department": "Physics"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
