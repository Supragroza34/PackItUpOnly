from types import SimpleNamespace
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from KCLTicketingSystems.models import Reply, Ticket, User
from KCLTicketingSystems.serializers import ReplyCreateSerializer, ReplySerializer


class TicketConversationApiTests(APITestCase):
    """Group ticket conversation feature checks so the user workflow is guarded against regressions."""
    def setUp(self):
        """Establish shared fixtures so tests stay focused on behavior rather than setup details."""
        self.client = APIClient()
        self.owner = User.objects.create_user(
            username="owner",
            email="owner@kcl.ac.uk",
            password="Pass123!",
            role=User.Role.STUDENT,
            first_name="Olivia",
            last_name="Owner",
        )
        self.other_student = User.objects.create_user(
            username="other",
            email="other@kcl.ac.uk",
            password="Pass123!",
            role=User.Role.STUDENT,
        )
        self.staff = User.objects.create_user(
            username="staff1",
            email="staff1@kcl.ac.uk",
            password="Pass123!",
            role=User.Role.STAFF,
            first_name="Sam",
            last_name="Staff",
        )
        self.unassigned_staff = User.objects.create_user(
            username="staff2",
            email="staff2@kcl.ac.uk",
            password="Pass123!",
            role=User.Role.STAFF,
        )
        self.admin = User.objects.create_user(
            username="admin1",
            email="admin1@kcl.ac.uk",
            password="Pass123!",
            role=User.Role.ADMIN,
        )
        self.superuser = User.objects.create_user(
            username="root",
            email="root@kcl.ac.uk",
            password="Pass123!",
            role=User.Role.STUDENT,
            is_superuser=True,
        )
        self.ticket = Ticket.objects.create(
            user=self.owner,
            department="IT",
            type_of_issue="Login",
            additional_details="Cannot sign in",
            status=Ticket.Status.IN_PROGRESS,
            assigned_to=self.staff,
        )

    def _conversation_url(self, ticket_id=None):
        """Support the ticket conversation feature tests by conversation url so assertions remain focused on outcomes."""
        return f"/api/tickets/{ticket_id or self.ticket.id}/replies/"

    def _staff_url(self, ticket_id=None):
        """Support the ticket conversation feature tests by staff url so assertions remain focused on outcomes."""
        return f"/api/staff/dashboard/reply/{ticket_id or self.ticket.id}/"

    def test_ticket_replies_requires_authentication(self):
        """Guard ticket replies requires authentication in the ticket conversation feature flow so regressions surface early."""
        response = self.client.get(self._conversation_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owner_can_get_conversation_replies_in_order(self):
        """Guard owner can get conversation replies in order in the ticket conversation feature flow so regressions surface early."""
        Reply.objects.create(user=self.staff, ticket=self.ticket, body="Staff reply")
        Reply.objects.create(user=self.owner, ticket=self.ticket, body="Student follow up")

        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self._conversation_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["body"] for item in response.data], ["Staff reply", "Student follow up"])
        self.assertEqual(response.data[0]["user_role"], "staff")
        self.assertEqual(response.data[1]["user_role"], "student")

    def test_owner_can_post_reply_to_own_ticket(self):
        """Guard owner can post reply to own ticket in the ticket conversation feature flow so regressions surface early."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self._conversation_url(), {"body": "More details from student"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Reply.objects.filter(ticket=self.ticket, user=self.owner, body="More details from student").exists())

    def test_assigned_staff_can_post_reply(self):
        """Guard assigned staff can post reply in the ticket conversation feature flow so regressions surface early."""
        self.client.force_authenticate(user=self.staff)
        response = self.client.post(self._conversation_url(), {"body": "Here is help"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Reply.objects.filter(ticket=self.ticket, user=self.staff, body="Here is help").exists())

    def test_owner_can_post_nested_reply(self):
        parent = Reply.objects.create(user=self.staff, ticket=self.ticket, body="Can you confirm?")
        self.client.force_authenticate(user=self.owner)

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
        other_ticket = Ticket.objects.create(
            user=self.owner,
            department="IT",
            type_of_issue="Network",
            additional_details="VPN issue",
            status=Ticket.Status.IN_PROGRESS,
            assigned_to=self.staff,
        )
        other_parent = Reply.objects.create(
            user=self.staff,
            ticket=other_ticket,
            body="Reply on other ticket",
        )

        self.client.force_authenticate(user=self.owner)
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
        self.client.force_authenticate(user=self.staff)

        response = self.client.post(self._conversation_url(), {"body": "Please confirm this fix"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.AWAITING_RESPONSE)

    def test_student_reply_sets_ticket_back_to_in_progress(self):
        self.ticket.status = Ticket.Status.AWAITING_RESPONSE
        self.ticket.save(update_fields=["status"])
        self.client.force_authenticate(user=self.owner)

        response = self.client.post(self._conversation_url(), {"body": "I still need help"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.IN_PROGRESS)

    def test_dashboard_fetch_auto_closes_stale_awaiting_response_ticket(self):
        self.ticket.status = Ticket.Status.AWAITING_RESPONSE
        self.ticket.save(update_fields=["status"])

        old_reply = Reply.objects.create(user=self.staff, ticket=self.ticket, body="Waiting for your response")
        Reply.objects.filter(id=old_reply.id).update(created_at=timezone.now() - timedelta(days=4))

        self.client.force_authenticate(user=self.owner)
        response = self.client.get("/api/dashboard/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.CLOSED)

    def test_admin_can_access_ticket_conversation(self):
        """Guard admin can access ticket conversation in the ticket conversation feature flow so regressions surface early."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self._conversation_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_superuser_can_access_ticket_conversation(self):
        """Guard superuser can access ticket conversation in the ticket conversation feature flow so regressions surface early."""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self._conversation_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_other_student_cannot_access_ticket_conversation(self):
        """Guard other student cannot access ticket conversation in the ticket conversation feature flow so regressions surface early."""
        self.client.force_authenticate(user=self.other_student)
        response = self.client.get(self._conversation_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"], "Access denied")

    def test_unassigned_staff_cannot_access_ticket_conversation(self):
        """Guard unassigned staff cannot access ticket conversation in the ticket conversation feature flow so regressions surface early."""
        self.client.force_authenticate(user=self.unassigned_staff)
        response = self.client.get(self._conversation_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_post_reply_to_closed_ticket(self):
        """Guard cannot post reply to closed ticket in the ticket conversation feature flow so regressions surface early."""
        self.ticket.status = Ticket.Status.CLOSED
        self.ticket.save()
        self.client.force_authenticate(user=self.owner)

        response = self.client.post(self._conversation_url(), {"body": "Late reply"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("closed", response.data["error"].lower())

    def test_staff_reply_endpoint_rejects_student(self):
        """Guard staff reply endpoint rejects student in the ticket conversation feature flow so regressions surface early."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self._staff_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_reply_endpoint_lists_replies_for_assigned_staff(self):
        """Guard staff reply endpoint lists replies for assigned staff in the ticket conversation feature flow so regressions surface early."""
        Reply.objects.create(user=self.staff, ticket=self.ticket, body="Assigned staff response")
        self.client.force_authenticate(user=self.staff)

        response = self.client.get(self._staff_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["body"], "Assigned staff response")

    def test_staff_reply_endpoint_creates_reply_for_assigned_staff(self):
        """Guard staff reply endpoint creates reply for assigned staff in the ticket conversation feature flow so regressions surface early."""
        self.client.force_authenticate(user=self.staff)

        response = self.client.post(self._staff_url(), {"body": "Staff dashboard reply"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Reply.objects.filter(ticket=self.ticket, user=self.staff, body="Staff dashboard reply").exists())

    def test_staff_reply_endpoint_rejects_closed_ticket(self):
        """Guard staff reply endpoint rejects closed ticket in the ticket conversation feature flow so regressions surface early."""
        self.ticket.status = Ticket.Status.CLOSED
        self.ticket.save()
        self.client.force_authenticate(user=self.staff)

        response = self.client.post(self._staff_url(), {"body": "Should fail"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("closed", response.data["error"].lower())

    def test_staff_reply_endpoint_rejects_unassigned_staff(self):
        """Guard staff reply endpoint rejects unassigned staff in the ticket conversation feature flow so regressions surface early."""
        self.client.force_authenticate(user=self.unassigned_staff)
        response = self.client.get(self._staff_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_reply_view_accepts_valid_payload(self):
        """Guard create reply view accepts valid payload in the ticket conversation feature flow so regressions surface early."""
        self.client.force_authenticate(user=self.staff)

        response = self.client.post(
            "/api/replies/create/",
            {"ticket": self.ticket.id, "body": "Direct create view reply"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Reply.objects.filter(ticket=self.ticket, user=self.staff, body="Direct create view reply").exists())

    def test_create_reply_view_rejects_invalid_payload(self):
        """Guard create reply view rejects invalid payload in the ticket conversation feature flow so regressions surface early."""
        self.client.force_authenticate(user=self.staff)

        response = self.client.post(
            "/api/replies/create/",
            {"ticket": self.ticket.id, "body": "   "},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("blank", str(response.data["body"][0]).lower())

    def test_ticket_replies_rejects_invalid_payload(self):
        """Guard ticket replies rejects invalid payload in the ticket conversation feature flow so regressions surface early."""
        self.client.force_authenticate(user=self.owner)

        response = self.client.post(self._conversation_url(), {"body": ""}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("blank", str(response.data["body"][0]).lower())

    def test_staff_reply_endpoint_rejects_invalid_payload(self):
        """Guard staff reply endpoint rejects invalid payload in the ticket conversation feature flow so regressions surface early."""
        self.client.force_authenticate(user=self.staff)

        response = self.client.post(self._staff_url(), {"body": ""}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("blank", str(response.data["body"][0]).lower())

    def test_staff_reply_endpoint_requires_authentication(self):
        """Guard staff reply endpoint requires authentication in the ticket conversation feature flow so regressions surface early."""
        response = self.client.get(self._staff_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ReplySerializerTests(TestCase):
    """Group ticket conversation feature checks so the user workflow is guarded against regressions."""
    def setUp(self):
        """Establish shared fixtures so tests stay focused on behavior rather than setup details."""
        self.ticket = Ticket.objects.create(
            department="IT",
            type_of_issue="General",
            additional_details="Something happened",
            status=Ticket.Status.PENDING,
        )

    def test_reply_serializer_returns_student_role_for_missing_user(self):
        """Guard reply serializer returns student role for missing user in the ticket conversation feature flow so regressions surface early."""
        serializer = ReplySerializer()
        self.assertEqual(serializer.get_user_role(SimpleNamespace(user=None)), "student")

    def test_reply_serializer_returns_admin_for_superuser(self):
        """Guard reply serializer returns admin for superuser in the ticket conversation feature flow so regressions surface early."""
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
        """Guard reply create serializer strips body in the ticket conversation feature flow so regressions surface early."""
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
        """Guard reply create serializer rejects closed ticket in the ticket conversation feature flow so regressions surface early."""
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
    """Group ticket conversation feature checks so the user workflow is guarded against regressions."""
    def setUp(self):
        """Establish shared fixtures so tests stay focused on behavior rather than setup details."""
        self.client = APIClient()
        self.student = User.objects.create_user(
            username="dashstudent",
            email="dashstudent@kcl.ac.uk",
            password="Pass123!",
            role=User.Role.STUDENT,
            k_number="K000001",
        )
        self.staff = User.objects.create_user(
            username="dashstaff",
            email="dashstaff@kcl.ac.uk",
            password="Pass123!",
            role=User.Role.STAFF,
        )
        self.ticket = Ticket.objects.create(
            user=self.student,
            department="IT",
            type_of_issue="WiFi",
            additional_details="Drops out often",
            status=Ticket.Status.CLOSED,
            closed_by=self.staff,
        )
        Reply.objects.create(user=self.staff, ticket=self.ticket, body="Initial reply")
        Reply.objects.create(user=self.student, ticket=self.ticket, body="Follow up")

    def test_dashboard_returns_replies_in_chronological_order_and_closed_by_role(self):
        """Guard dashboard returns replies in chronological order and closed by role in the ticket conversation feature flow so regressions surface early."""
        self.client.force_authenticate(user=self.student)

        response = self.client.get("/api/dashboard/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ticket_data = response.json()["tickets"][0]
        self.assertEqual(ticket_data["closed_by_role"], "staff")
        self.assertEqual([reply["body"] for reply in ticket_data["replies"]], ["Initial reply", "Follow up"])
        self.assertEqual(ticket_data["replies"][0]["user_role"], "staff")
        self.assertEqual(ticket_data["replies"][1]["user_role"], "student")

    def test_student_can_close_own_ticket(self):
        """Guard student can close own ticket in the ticket conversation feature flow so regressions surface early."""
        open_ticket = Ticket.objects.create(
            user=self.student,
            department="IT",
            type_of_issue="Mouse",
            additional_details="Stops working",
            status=Ticket.Status.PENDING,
        )
        self.client.force_authenticate(user=self.student)

        response = self.client.post(f"/api/dashboard/tickets/{open_ticket.id}/close/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        open_ticket.refresh_from_db()
        self.assertEqual(open_ticket.status, Ticket.Status.CLOSED)
        self.assertEqual(open_ticket.closed_by, self.student)

    def test_student_cannot_close_someone_elses_ticket(self):
        """Guard student cannot close someone elses ticket in the ticket conversation feature flow so regressions surface early."""
        other_student = User.objects.create_user(
            username="otherdash",
            email="otherdash@kcl.ac.uk",
            password="Pass123!",
            role=User.Role.STUDENT,
        )
        other_ticket = Ticket.objects.create(
            user=other_student,
            department="IT",
            type_of_issue="Keyboard",
            additional_details="Keys stuck",
            status=Ticket.Status.PENDING,
        )
        self.client.force_authenticate(user=self.student)

        response = self.client.post(f"/api/dashboard/tickets/{other_ticket.id}/close/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_student_cannot_close_ticket_twice(self):
        """Guard student cannot close ticket twice in the ticket conversation feature flow so regressions surface early."""
        self.client.force_authenticate(user=self.student)

        response = self.client.post(f"/api/dashboard/tickets/{self.ticket.id}/close/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already closed", response.data["error"].lower())
