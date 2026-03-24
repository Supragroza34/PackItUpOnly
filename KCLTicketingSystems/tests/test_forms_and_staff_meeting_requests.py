from datetime import timedelta, time

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from KCLTicketingSystems.forms import ReplyForm
from KCLTicketingSystems.models import MeetingRequest, OfficeHours, Reply, Ticket, User


class ReplyFormTests(TestCase):
    """Group forms and staff meeting requests checks so the user workflow is guarded against regressions."""
    def setUp(self):
        """Establish shared fixtures so tests stay focused on behavior rather than setup details."""
        self.student = User.objects.create_user(
            username="student_form",
            email="student_form@example.com",
            password="pass123",
            role=User.Role.STUDENT,
        )
        self.staff = User.objects.create_user(
            username="staff_form",
            email="staff_form@example.com",
            password="pass123",
            role=User.Role.STAFF,
        )
        self.ticket = Ticket.objects.create(
            user=self.student,
            department="Informatics",
            type_of_issue="Login Issue",
            additional_details="Cannot log in",
        )

    def test_reply_form_meta_and_valid_payload(self):
        """Guard reply form meta and valid payload in the forms and staff meeting requests flow so regressions surface early."""
        self.assertEqual(ReplyForm.Meta.model, Reply)
        self.assertEqual(ReplyForm.Meta.fields, ["body"])
        form = ReplyForm(data={"body": "Test reply"})
        self.assertTrue(form.is_valid())

    def test_reply_form_requires_body(self):
        """Guard reply form requires body in the forms and staff meeting requests flow so regressions surface early."""
        form = ReplyForm(data={"body": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("body", form.errors)


class StaffMeetingRequestsViewTests(TestCase):
    """Group forms and staff meeting requests checks so the user workflow is guarded against regressions."""
    def setUp(self):
        """Establish shared fixtures so tests stay focused on behavior rather than setup details."""
        self.client = APIClient()

        self.student = User.objects.create_user(
            username="student_meeting",
            email="student_meeting@example.com",
            password="pass123",
            first_name="Stu",
            last_name="Dent",
            role=User.Role.STUDENT,
        )
        self.staff = User.objects.create_user(
            username="staff_meeting",
            email="staff_meeting@example.com",
            password="pass123",
            first_name="Sta",
            last_name="Ff",
            role=User.Role.STAFF,
        )
        self.staff2 = User.objects.create_user(
            username="staff_meeting_2",
            email="staff_meeting2@example.com",
            password="pass123",
            first_name="Other",
            last_name="Staff",
            role=User.Role.STAFF,
        )
        self.admin = User.objects.create_user(
            username="admin_meeting",
            email="admin_meeting@example.com",
            password="pass123",
            role=User.Role.ADMIN,
        )

        self.meeting_datetime = timezone.now() + timedelta(days=1)
        day_name = self.meeting_datetime.strftime("%A")
        meeting_time = self.meeting_datetime.time()
        start_hour = max(0, meeting_time.hour - 1)
        end_hour = min(23, meeting_time.hour + 1)

        OfficeHours.objects.create(
            staff=self.staff,
            day_of_week=day_name,
            start_time=time(start_hour, 0),
            end_time=time(end_hour, 59),
        )

        self.pending_request = MeetingRequest.objects.create(
            student=self.student,
            staff=self.staff,
            meeting_datetime=self.meeting_datetime,
            description="Need help with coursework",
        )

    def _auth(self, user):
        """Support the forms and staff meeting requests tests by auth so assertions remain focused on outcomes."""
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_meeting_request_list_staff_only_and_success(self):
        """Guard meeting request list staff only and success in the forms and staff meeting requests flow so regressions surface early."""
        self._auth(self.student)
        denied = self.client.get("/api/staff/dashboard/meeting-requests/")
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        self._auth(self.staff)
        ok = self.client.get("/api/staff/dashboard/meeting-requests/")
        self.assertEqual(ok.status_code, status.HTTP_200_OK)
        self.assertEqual(len(ok.data), 1)

    def test_accept_and_deny_request_paths(self):
        """Guard accept and deny request paths in the forms and staff meeting requests flow so regressions surface early."""
        self._auth(self.staff)
        accepted = self.client.post(
            f"/api/staff/dashboard/meeting-requests/{self.pending_request.id}/accept/"
        )
        self.assertEqual(accepted.status_code, status.HTTP_200_OK)
        self.pending_request.refresh_from_db()
        self.assertEqual(self.pending_request.status, MeetingRequest.Status.ACCEPTED)

        processed = self.client.post(
            f"/api/staff/dashboard/meeting-requests/{self.pending_request.id}/accept/"
        )
        self.assertEqual(processed.status_code, status.HTTP_400_BAD_REQUEST)

        to_deny = MeetingRequest.objects.create(
            student=self.student,
            staff=self.staff,
            meeting_datetime=self.meeting_datetime,
            description="Another request",
        )
        denied = self.client.post(f"/api/staff/dashboard/meeting-requests/{to_deny.id}/deny/")
        self.assertEqual(denied.status_code, status.HTTP_200_OK)
        to_deny.refresh_from_db()
        self.assertEqual(to_deny.status, MeetingRequest.Status.DENIED)

        deny_again = self.client.post(f"/api/staff/dashboard/meeting-requests/{to_deny.id}/deny/")
        self.assertEqual(deny_again.status_code, status.HTTP_400_BAD_REQUEST)

    def test_office_hours_manage_and_delete(self):
        """Guard office hours manage and delete in the forms and staff meeting requests flow so regressions surface early."""
        self._auth(self.student)
        forbidden = self.client.get("/api/staff/office-hours/")
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

        self._auth(self.staff)
        listed = self.client.get("/api/staff/office-hours/")
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(listed.data), 1)

        create_payload = {
            "day_of_week": self.meeting_datetime.strftime("%A"),
            "start_time": "09:00:00",
            "end_time": "11:00:00",
        }
        created = self.client.post("/api/staff/office-hours/", create_payload, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        bad_payload = {
            "day_of_week": "NotADay",
            "start_time": "11:00:00",
            "end_time": "10:00:00",
        }
        bad = self.client.post("/api/staff/office-hours/", bad_payload, format="json")
        self.assertEqual(bad.status_code, status.HTTP_400_BAD_REQUEST)

        hours_id = created.data["id"]
        deleted = self.client.delete(f"/api/staff/office-hours/{hours_id}/")
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)

    def test_meeting_request_create_get_and_post(self):
        """Guard meeting request create get and post in the forms and staff meeting requests flow so regressions surface early."""
        self._auth(self.student)
        listed = self.client.get("/api/meeting-requests/")
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listed.data), 1)

        payload = {
            "staff": self.staff.id,
            "meeting_datetime": self.meeting_datetime.isoformat(),
            "description": "Can we discuss lab work?",
        }
        created = self.client.post("/api/meeting-requests/", payload, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        invalid_payload = {
            "staff": self.staff2.id,
            "meeting_datetime": (self.meeting_datetime + timedelta(hours=2)).isoformat(),
            "description": "Outside office hours",
        }
        invalid = self.client.post("/api/meeting-requests/", invalid_payload, format="json")
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
