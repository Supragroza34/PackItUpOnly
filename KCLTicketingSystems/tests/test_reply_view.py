from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from KCLTicketingSystems.models import Ticket, Reply, User

class ReplyCreateViewTests(APITestCase):

    def setUp(self):
        # Create users
        self.staff = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            k_number='22222222',
            role=User.Role.STAFF
        )
        
        # Create test user for ticket
        self.ticket_user = User.objects.create_user(
            username='ticketuser',
            email='ticketuser@test.com',
            password='testpass123',
            first_name='John',
            last_name='Doe',
            k_number='12345678',
            role=User.Role.STUDENT
        )

        # Create test ticket
        self.ticket = Ticket.objects.create(
            user=self.ticket_user,
            department='Informatics',
            type_of_issue='Software Installation Issues',
            additional_details='Need help with software',
            status=Ticket.Status.PENDING
        )

        self.url = f'/api/replies/create/'

    def test_authenticated_user_can_post_reply(self):
        refresh = RefreshToken.for_user(self.staff)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )
        data = {
            "user": self.staff.id,
            "ticket": self.ticket.id,
            "body": "This is a test reply",
        }

        count_before = Reply.objects.count()
        response = self.client.post(self.url, data)
        count_after = Reply.objects.count()
        created_reply = Reply.objects.get(ticket=self.ticket)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(count_before, count_after-1)
        self.assertEqual(created_reply.body, "This is a test reply")

    def test_unauthenticated_user_cannot_post_reply(self):
        data = {
            "user": self.ticket_user.id,
            "ticket": self.ticket.id,
            "body": "Unauthorized comment",
        }

        count_before = Reply.objects.count()
        response = self.client.post(self.url, data)
        count_after = Reply.objects.count()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(count_after, count_before)        

    def test_reply_is_linked_to_logged_in_staff(self):

        refresh = RefreshToken.for_user(self.staff)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )
        data = {
            "user": self.staff.id,
            "ticket": self.ticket.id,
            "body": "User link test"
        }

        self.client.post(self.url, data)

        reply = Reply.objects.first()
        self.assertEqual(reply.user, self.staff)

    def test_invalid_reply_post_no_body(self):
        refresh = RefreshToken.for_user(self.staff)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )
        data = {
            "user": self.staff.id,
            "ticket": self.ticket.id,
            "body": "",
        }

        count_before = Reply.objects.count()
        response = self.client.post(self.url, data)
        count_after = Reply.objects.count()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(count_before, count_after)

    def test_invalid_reply_post_no_ticket(self):
        refresh = RefreshToken.for_user(self.staff)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )
        data = {
            "user": self.staff.id,
            "ticket": "",
            "body": "Body present",
        }

        count_before = Reply.objects.count()
        response = self.client.post(self.url, data)
        count_after = Reply.objects.count()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(count_before, count_after)


class ReplyDetailsViewTests(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="student_reply",
            email="student_reply@test.com",
            password="testpass123",
            role=User.Role.STUDENT,
            k_number="30000001",
        )
        self.staff = User.objects.create_user(
            username="staff_reply",
            email="staff_reply@test.com",
            password="testpass123",
            role=User.Role.STAFF,
            k_number="30000002",
        )
        self.other_staff = User.objects.create_user(
            username="other_staff_reply",
            email="other_staff_reply@test.com",
            password="testpass123",
            role=User.Role.STAFF,
            k_number="30000003",
        )
        self.admin = User.objects.create_user(
            username="admin_reply",
            email="admin_reply@test.com",
            password="testpass123",
            role=User.Role.ADMIN,
            is_superuser=True,
            k_number="30000004",
        )

        self.ticket = Ticket.objects.create(
            user=self.student,
            assigned_to=self.staff,
            department="Informatics",
            type_of_issue="Software Installation Issues",
            additional_details="Need help with setup",
            status=Ticket.Status.PENDING,
        )
        self.url = f"/api/staff/dashboard/reply/{self.ticket.id}/"

    def test_unauthenticated_user_gets_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_user_gets_403(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unassigned_staff_gets_access_denied(self):
        self.client.force_authenticate(user=self.other_staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("error"), "Access denied")

    def test_assigned_staff_get_lists_replies(self):
        Reply.objects.create(user=self.staff, ticket=self.ticket, body="First")
        Reply.objects.create(user=self.staff, ticket=self.ticket, body="Second")

        self.client.force_authenticate(user=self.staff)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["body"], "First")
        self.assertEqual(response.data[1]["body"], "Second")

    def test_assigned_staff_post_creates_reply(self):
        self.client.force_authenticate(user=self.staff)

        response = self.client.post(self.url, {"body": "Staff reply"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reply.objects.filter(ticket=self.ticket).count(), 1)
        created = Reply.objects.get(ticket=self.ticket)
        self.assertEqual(created.user, self.staff)
        self.assertEqual(created.body, "Staff reply")

    def test_assigned_staff_post_invalid_payload_returns_400(self):
        self.client.force_authenticate(user=self.staff)

        response = self.client.post(self.url, {"body": ""}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_can_access_unassigned_ticket(self):
        ticket = Ticket.objects.create(
            user=self.student,
            assigned_to=None,
            department="Informatics",
            type_of_issue="Other",
            additional_details="Admin access check",
        )
        url = f"/api/staff/dashboard/reply/{ticket.id}/"
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_superuser_with_non_admin_role_can_access(self):
        super_staff = User.objects.create_user(
            username="super_staff_reply",
            email="super_staff_reply@test.com",
            password="testpass123",
            role=User.Role.STUDENT,
            is_superuser=True,
            k_number="30000005",
        )
        ticket = Ticket.objects.create(
            user=self.student,
            assigned_to=None,
            department="Informatics",
            type_of_issue="Superuser check",
            additional_details="Needs privileged access",
        )
        url = f"/api/staff/dashboard/reply/{ticket.id}/"
        self.client.force_authenticate(user=super_staff)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ticket_not_found_returns_404(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/staff/dashboard/reply/999999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)