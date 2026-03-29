from rest_framework import status
from rest_framework.test import APITestCase

from KCLTicketingSystems.models import User


class StaffDirectoryViewTests(APITestCase):
    STAFF_DIRECTORY_URL = "/api/staff/"

    def setUp(self):
        self.url = self.STAFF_DIRECTORY_URL
        self._create_users()

    def _create_users(self):
        users = {
            "student": ("student_dir", "student_dir@test.com", User.Role.STUDENT, "Student", "User", "Informatics", "81000001"),
            "staff_a": ("staff_a_dir", "staff_a_dir@test.com", User.Role.STAFF, "Alice", "Brown", "informatics", "81000002"),
            "staff_b": ("staff_b_dir", "staff_b_dir@test.com", User.Role.STAFF, "Bob", "Anderson", "Informatics", "81000003"),
            "staff_c": ("staff_c_dir", "staff_c_dir@test.com", User.Role.STAFF, "Carol", "Smith", "Maths", "81000004"),
        }
        for attr, args in users.items():
            setattr(self, attr, self._create_user(*args))

    def _create_user(self, username, email, role, first_name, last_name, department, k_number):
        return User.objects.create_user(
            username=username,
            email=email,
            password="testpass123",
            role=role,
            first_name=first_name,
            last_name=last_name,
            department=department,
            k_number=k_number,
        )

    def _auth_as_student(self):
        self.client.force_authenticate(user=self.student)

    @staticmethod
    def _returned_ids(response):
        return [item["id"] for item in response.data]

    def test_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_only_staff_users(self):
        self._auth_as_student()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = self._returned_ids(response)
        self.assertNotIn(self.student.id, returned_ids)
        self.assertIn(self.staff_a.id, returned_ids)
        self.assertIn(self.staff_b.id, returned_ids)
        self.assertIn(self.staff_c.id, returned_ids)

    def test_department_filter_is_case_insensitive(self):
        self._auth_as_student()
        response = self.client.get(self.url, {"department": "informatics"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = self._returned_ids(response)
        self.assertIn(self.staff_a.id, returned_ids)
        self.assertIn(self.staff_b.id, returned_ids)
        self.assertNotIn(self.staff_c.id, returned_ids)

    def test_results_are_ordered_by_last_name_then_first_name(self):
        self._auth_as_student()
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
        self._auth_as_student()
        response = self.client.get(self.url, {"department": "Physics"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
