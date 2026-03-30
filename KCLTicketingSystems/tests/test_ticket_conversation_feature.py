"""Tests for Ticket Conversation Feature."""

from types import SimpleNamespace
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from KCLTicketingSystems.models import Reply, Ticket, User
from KCLTicketingSystems.serializers import ReplyCreateSerializer, ReplySerializer


class TicketConversationApiTests(APITestCase):
    REPLY_CREATE_URL = "/api/replies/create/"
    DASHBOARD_URL = "/api/dashboard/"

    def setUp(self):
        self.client = APIClient()
        self._create_users()
        self.ticket = self._create_ticket(self.owner, self.staff, "Login", "Cannot sign in")

    def _create_user(self, username, email, role, **extra):
        return User.objects.create_user(
            username=username,
            email=email,
            password="Pass123!",
            role=role,
            **extra,
        )

    def _create_users(self):
        self.owner = self._create_user(
            "owner",
            "owner@kcl.ac.uk",
            User.Role.STUDENT,
            first_name="Olivia",
            last_name="Owner",
        )
        self.other_student = self._create_user("other", "other@kcl.ac.uk", User.Role.STUDENT)
        self.staff = self._create_user(
            "staff1",
            "staff1@kcl.ac.uk",
            User.Role.STAFF,
            first_name="Sam",
            last_name="Staff",
        )
        self.unassigned_staff = self._create_user("staff2", "staff2@kcl.ac.uk", User.Role.STAFF)
        self.admin = self._create_user("admin1", "admin1@kcl.ac.uk", User.Role.ADMIN)
        self.superuser = self._create_user(
            "root",
            "root@kcl.ac.uk",
            User.Role.STUDENT,
            is_superuser=True,
        )

    def _create_ticket(self, user, assigned_to, issue, details, status=Ticket.Status.IN_PROGRESS):
        return Ticket.objects.create(
            user=user,
            department="IT",
            type_of_issue=issue,
            additional_details=details,
            status=status,
            assigned_to=assigned_to,
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def _conversation_url(self, ticket_id=None):
        return f"/api/tickets/{ticket_id or self.ticket.id}/replies/"

    def _staff_url(self, ticket_id=None):
        return f"/api/staff/dashboard/reply/{ticket_id or self.ticket.id}/"

    def test_ticket_replies_requires_authentication(self):
        response = self.client.get(self._conversation_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owner_can_get_conversation_replies_in_order(self):
        Reply.objects.create(user=self.staff, ticket=self.ticket, body="Staff reply")
        Reply.objects.create(user=self.owner, ticket=self.ticket, body="Student follow up")

        self._auth(self.owner)
        response = self.client.get(self._conversation_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["body"] for item in response.data], ["Staff reply", "Student follow up"])
        self.assertEqual(response.data[0]["user_role"], "staff")
        self.assertEqual(response.data[1]["user_role"], "student")

    def test_owner_can_post_reply_to_own_ticket(self):
        self._auth(self.owner)
        response = self.client.post(self._conversation_url(), {"body": "More details from student"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Reply.objects.filter(ticket=self.ticket, user=self.owner, body="More details from student").exists())

    def test_assigned_staff_can_post_reply(self):
        self._auth(self.staff)
        response = self.client.post(self._conversation_url(), {"body": "Here is help"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Reply.objects.filter(ticket=self.ticket, user=self.staff, body="Here is help").exists())

    def test_owner_can_post_nested_reply(self):
        parent = Reply.objects.create(user=self.staff, ticket=self.ticket, body="Can you confirm?")
        self._auth(self.owner)

        response = self.client.post(
            self._conversation_url(),
            {"body": "Yes, still broken", "parent": parent.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Reply.objects.get(ticket=self.ticket, body="Yes, still broken")
        self.assertEqual(created.parent_id, parent.id)

        get_response = self.client.get(self._conversation_url())
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data[0]["id"], parent.id)
        self.assertEqual(get_response.data[0]["children"][0]["parent"], parent.id)

    def test_rejects_parent_from_another_ticket(self):
        other_ticket = self._create_ticket(self.owner, self.staff, "Network", "VPN issue")
        other_parent = Reply.objects.create(
            user=self.staff,
            ticket=other_ticket,
            body="Reply on other ticket",
        )

        self._auth(self.owner)
        response = self.client.post(
            self._conversation_url(),
            {"body": "invalid parent", "parent": other_parent.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("same ticket", str(response.data["parent"][0]).lower())

    def test_staff_reply_sets_ticket_to_awaiting_response(self):
        self.ticket.status = Ticket.Status.IN_PROGRESS
        self.ticket.save(update_fields=["status"])
        self._auth(self.staff)

        response = self.client.post(self._conversation_url(), {"body": "Please confirm this fix"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.AWAITING_RESPONSE)

    def test_student_reply_sets_ticket_back_to_in_progress(self):
        self.ticket.status = Ticket.Status.AWAITING_RESPONSE
        self.ticket.save(update_fields=["status"])
        self._auth(self.owner)

        response = self.client.post(self._conversation_url(), {"body": "I still need help"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.IN_PROGRESS)

    def test_dashboard_fetch_auto_closes_stale_awaiting_response_ticket(self):
        self.ticket.status = Ticket.Status.AWAITING_RESPONSE
        self.ticket.save(update_fields=["status"])

        old_reply = Reply.objects.create(user=self.staff, ticket=self.ticket, body="Waiting for your response")
        Reply.objects.filter(id=old_reply.id).update(created_at=timezone.now() - timedelta(days=4))

        self._auth(self.owner)
        response = self.client.get(self.DASHBOARD_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.CLOSED)

    def test_admin_can_access_ticket_conversation(self):
        self._auth(self.admin)
        response = self.client.get(self._conversation_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_superuser_can_access_ticket_conversation(self):
        self._auth(self.superuser)
        response = self.client.get(self._conversation_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_other_student_cannot_access_ticket_conversation(self):
        self._auth(self.other_student)
        response = self.client.get(self._conversation_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"], "Access denied")

    def test_unassigned_staff_cannot_access_ticket_conversation(self):
        self._auth(self.unassigned_staff)
        response = self.client.get(self._conversation_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_post_reply_to_closed_ticket(self):
        self.ticket.status = Ticket.Status.CLOSED
        self.ticket.save()
        self._auth(self.owner)

        response = self.client.post(self._conversation_url(), {"body": "Late reply"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("closed", response.data["error"].lower())

    def test_staff_reply_endpoint_rejects_student(self):
        self._auth(self.owner)
        response = self.client.get(self._staff_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_reply_endpoint_lists_replies_for_assigned_staff(self):
        Reply.objects.create(user=self.staff, ticket=self.ticket, body="Assigned staff response")
        self._auth(self.staff)

        response = self.client.get(self._staff_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["body"], "Assigned staff response")

    def test_staff_reply_endpoint_creates_reply_for_assigned_staff(self):
        self._auth(self.staff)

        response = self.client.post(self._staff_url(), {"body": "Staff dashboard reply"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Reply.objects.filter(ticket=self.ticket, user=self.staff, body="Staff dashboard reply").exists())

    def test_staff_reply_endpoint_rejects_closed_ticket(self):
        self.ticket.status = Ticket.Status.CLOSED
        self.ticket.save()
        self._auth(self.staff)

        response = self.client.post(self._staff_url(), {"body": "Should fail"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("closed", response.data["error"].lower())

    def test_staff_reply_endpoint_rejects_unassigned_staff(self):
        self._auth(self.unassigned_staff)
        response = self.client.get(self._staff_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_reply_view_accepts_valid_payload(self):
        self._auth(self.staff)

        response = self.client.post(
            self.REPLY_CREATE_URL,
            {"ticket": self.ticket.id, "body": "Direct create view reply"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Reply.objects.filter(ticket=self.ticket, user=self.staff, body="Direct create view reply").exists())

    def test_create_reply_view_rejects_invalid_payload(self):
        self._auth(self.staff)

        response = self.client.post(
            self.REPLY_CREATE_URL,
            {"ticket": self.ticket.id, "body": "   "},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("blank", str(response.data["body"][0]).lower())

    def test_ticket_replies_rejects_invalid_payload(self):
        self._auth(self.owner)

        response = self.client.post(self._conversation_url(), {"body": ""}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("blank", str(response.data["body"][0]).lower())

    def test_staff_reply_endpoint_rejects_invalid_payload(self):
        self._auth(self.staff)

        response = self.client.post(self._staff_url(), {"body": ""}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("blank", str(response.data["body"][0]).lower())

    def test_staff_reply_endpoint_requires_authentication(self):
        response = self.client.get(self._staff_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ReplySerializerTests(TestCase):
    def setUp(self):
        self.ticket = Ticket.objects.create(
            department="IT",
            type_of_issue="General",
            additional_details="Something happened",
            status=Ticket.Status.PENDING,
        )

    def test_reply_serializer_returns_student_role_for_missing_user(self):
        serializer = ReplySerializer()
        self.assertEqual(serializer.get_user_role(SimpleNamespace(user=None)), "student")

    def test_reply_serializer_returns_admin_for_superuser(self):
        admin = User.objects.create_user(
            username="boss",
            email="boss@kcl.ac.uk",
            password="Pass123!",
            role=User.Role.STUDENT,
            is_superuser=True,
        )
        reply = Reply.objects.create(user=admin, ticket=self.ticket, body="Admin response")
        serializer = ReplySerializer(instance=reply)
        self.assertEqual(serializer.data["user_role"], "admin")

    def test_reply_create_serializer_strips_body(self):
        student = User.objects.create_user(
            username="student1",
            email="student1@kcl.ac.uk",
            password="Pass123!",
            role=User.Role.STUDENT,
        )
        ticket = Ticket.objects.create(
            user=student,
            department="IT",
            type_of_issue="General",
            additional_details="Need support",
            status=Ticket.Status.PENDING,
        )

        serializer = ReplyCreateSerializer(data={"ticket": ticket.id, "body": "  trimmed text  "})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["body"], "trimmed text")

    def test_reply_create_serializer_rejects_closed_ticket(self):
        student = User.objects.create_user(
            username="student2",
            email="student2@kcl.ac.uk",
            password="Pass123!",
            role=User.Role.STUDENT,
        )
        ticket = Ticket.objects.create(
            user=student,
            department="IT",
            type_of_issue="General",
            additional_details="Need support",
            status=Ticket.Status.CLOSED,
        )

        serializer = ReplyCreateSerializer(data={"ticket": ticket.id, "body": "Cannot add"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("Cannot add a reply to a closed ticket.", serializer.errors["ticket"][0])


class UserDashboardConversationTests(APITestCase):
    DASHBOARD_URL = "/api/dashboard/"

    def setUp(self):
        self.client = APIClient()
        self.student = self._create_user(
            "dashstudent",
            "dashstudent@kcl.ac.uk",
            User.Role.STUDENT,
            k_number="K000001",
        )
        self.staff = self._create_user("dashstaff", "dashstaff@kcl.ac.uk", User.Role.STAFF)
        self.ticket = self._create_ticket(
            user=self.student,
            issue="WiFi",
            details="Drops out often",
            status=Ticket.Status.CLOSED,
            closed_by=self.staff,
        )
        self._create_ticket_replies()

    def _create_user(self, username, email, role, **extra):
        return User.objects.create_user(
            username=username,
            email=email,
            password="Pass123!",
            role=role,
            **extra,
        )

    def _create_ticket(self, user, issue, details, status, closed_by=None):
        return Ticket.objects.create(
            user=user,
            department="IT",
            type_of_issue=issue,
            additional_details=details,
            status=status,
            closed_by=closed_by,
        )

    def _create_ticket_replies(self):
        Reply.objects.create(user=self.staff, ticket=self.ticket, body="Initial reply")
        Reply.objects.create(user=self.student, ticket=self.ticket, body="Follow up")

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_dashboard_returns_replies_in_chronological_order_and_closed_by_role(self):
        self._auth(self.student)

        response = self.client.get(self.DASHBOARD_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ticket_data = response.json()["tickets"][0]
        self.assertEqual(ticket_data["closed_by_role"], "staff")
        self.assertEqual([reply["body"] for reply in ticket_data["replies"]], ["Initial reply", "Follow up"])
        self.assertEqual(ticket_data["replies"][0]["user_role"], "staff")
        self.assertEqual(ticket_data["replies"][1]["user_role"], "student")

    def test_student_can_close_own_ticket(self):
        open_ticket = self._create_ticket(
            user=self.student,
            issue="Mouse",
            details="Stops working",
            status=Ticket.Status.PENDING,
        )
        self._auth(self.student)

        response = self.client.post(f"/api/dashboard/tickets/{open_ticket.id}/close/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        open_ticket.refresh_from_db()
        self.assertEqual(open_ticket.status, Ticket.Status.CLOSED)
        self.assertEqual(open_ticket.closed_by, self.student)

    def test_student_cannot_close_someone_elses_ticket(self):
        other_student = self._create_user("otherdash", "otherdash@kcl.ac.uk", User.Role.STUDENT)
        other_ticket = self._create_ticket(
            user=other_student,
            issue="Keyboard",
            details="Keys stuck",
            status=Ticket.Status.PENDING,
        )
        self._auth(self.student)

        response = self.client.post(f"/api/dashboard/tickets/{other_ticket.id}/close/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_student_cannot_close_ticket_twice(self):
        self._auth(self.student)

        response = self.client.post(f"/api/dashboard/tickets/{self.ticket.id}/close/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already closed", response.data["error"].lower())
