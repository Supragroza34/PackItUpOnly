from datetime import timedelta, time

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from KCLTicketingSystems.forms import ReplyForm
from KCLTicketingSystems.models import MeetingRequest, OfficeHours, Reply, Ticket, User


class ReplyFormTests(TestCase):
    def setUp(self):
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
        self.assertEqual(ReplyForm.Meta.model, Reply)
        self.assertEqual(ReplyForm.Meta.fields, ["body"])
        form = ReplyForm(data={"body": "Test reply"})
        self.assertTrue(form.is_valid())

    def test_reply_form_requires_body(self):
        form = ReplyForm(data={"body": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("body", form.errors)


class StaffMeetingRequestsViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self._create_users()
        self.meeting_datetime = self._build_meeting_datetime()
        self._create_staff_office_hours()
        self.pending_request = self._create_meeting_request(
            staff=self.staff,
            description="Need help with coursework",
        )

    def _create_users(self):
        self.student = self._create_user(
            "student_meeting",
            "student_meeting@example.com",
            User.Role.STUDENT,
            first_name="Stu",
            last_name="Dent",
        )
        self.staff = self._create_user(
            "staff_meeting",
            "staff_meeting@example.com",
            User.Role.STAFF,
            first_name="Sta",
            last_name="Ff",
        )
        self.staff2 = self._create_user(
            "staff_meeting_2",
            "staff_meeting2@example.com",
            User.Role.STAFF,
            first_name="Other",
            last_name="Staff",
        )
        self.admin = self._create_user("admin_meeting", "admin_meeting@example.com", User.Role.ADMIN)

    def _create_user(self, username, email, role, **extra):
        return User.objects.create_user(
            username=username,
            email=email,
            password="pass123",
            role=role,
            **extra,
        )

    def _build_meeting_datetime(self):
        dt = timezone.now() + timedelta(days=1)
        dt = dt.replace(second=0, microsecond=0)
        minute = ((dt.minute + 14) // 15) * 15
        if minute == 60:
            dt = dt + timedelta(hours=1)
            minute = 0
        return dt.replace(minute=minute)

    def _create_staff_office_hours(self):
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

    def _create_meeting_request(self, staff, description, offset_minutes=0):
        return MeetingRequest.objects.create(
            student=self.student,
            staff=staff,
            meeting_datetime=self.meeting_datetime + timedelta(minutes=offset_minutes),
            description=description,
        )

    def _meeting_requests_url(self):
        return "/api/staff/dashboard/meeting-requests/"

    def _meeting_action_url(self, request_id, action):
        return f"/api/staff/dashboard/meeting-requests/{request_id}/{action}/"

    def _office_hours_url(self):
        return "/api/staff/office-hours/"

    def _student_meeting_requests_url(self):
        return "/api/meeting-requests/"

    def _available_slots_url(self, staff_id, date_str=None):
        base = f"/api/staff/{staff_id}/available-slots/"
        return f"{base}?date={date_str}" if date_str else base

    def _auth(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_meeting_request_list_staff_only_and_success(self):
        self._auth(self.student)
        denied = self.client.get(self._meeting_requests_url())
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        self._auth(self.staff)
        ok = self.client.get(self._meeting_requests_url())
        self.assertEqual(ok.status_code, status.HTTP_200_OK)
        self.assertEqual(len(ok.data), 1)

    def test_accept_request_and_reaccept_fails(self):
        self._auth(self.staff)
        accepted = self.client.post(self._meeting_action_url(self.pending_request.id, "accept"))
        self.assertEqual(accepted.status_code, status.HTTP_200_OK)
        self.pending_request.refresh_from_db()
        self.assertEqual(self.pending_request.status, MeetingRequest.Status.ACCEPTED)

        processed = self.client.post(self._meeting_action_url(self.pending_request.id, "accept"))
        self.assertEqual(processed.status_code, status.HTTP_400_BAD_REQUEST)

    def test_deny_request_and_redeny_fails(self):
        self._auth(self.staff)
        to_deny = self._create_meeting_request(
            staff=self.staff,
            description="Another request",
            offset_minutes=30,
        )
        denied = self.client.post(self._meeting_action_url(to_deny.id, "deny"))
        self.assertEqual(denied.status_code, status.HTTP_200_OK)
        to_deny.refresh_from_db()
        self.assertEqual(to_deny.status, MeetingRequest.Status.DENIED)

        deny_again = self.client.post(self._meeting_action_url(to_deny.id, "deny"))
        self.assertEqual(deny_again.status_code, status.HTTP_400_BAD_REQUEST)

    def test_office_hours_list_requires_staff_role(self):
        self._auth(self.student)
        forbidden = self.client.get(self._office_hours_url())
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

        self._auth(self.staff)
        listed = self.client.get(self._office_hours_url())
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(listed.data), 1)

    def test_office_hours_create_and_delete(self):
        self._auth(self.staff)
        create_payload = {
            "day_of_week": self.meeting_datetime.strftime("%A"),
            "start_time": "09:00:00",
            "end_time": "11:00:00",
        }
        created = self.client.post(self._office_hours_url(), create_payload, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        hours_id = created.data["id"]
        deleted = self.client.delete(f"{self._office_hours_url()}{hours_id}/")
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)

    def test_office_hours_create_invalid_payload(self):
        self._auth(self.staff)

        bad_payload = {
            "day_of_week": "NotADay",
            "start_time": "11:00:00",
            "end_time": "10:00:00",
        }
        bad = self.client.post(self._office_hours_url(), bad_payload, format="json")
        self.assertEqual(bad.status_code, status.HTTP_400_BAD_REQUEST)

    def test_student_can_list_and_create_meeting_request(self):
        self._auth(self.student)
        listed = self.client.get(self._student_meeting_requests_url())
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listed.data), 1)

        payload = {
            "staff": self.staff.id,
            # Use a different (free) slot; the serializer blocks (staff, meeting_datetime)
            # conflicts for pending/accepted requests.
            "meeting_datetime": (self.meeting_datetime + timedelta(minutes=15)).isoformat(),
            "description": "Can we discuss lab work?",
        }
        created = self.client.post(self._student_meeting_requests_url(), payload, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

    def test_meeting_request_create_outside_office_hours_fails(self):
        self._auth(self.student)
        invalid_payload = {
            "staff": self.staff2.id,
            "meeting_datetime": (self.meeting_datetime + timedelta(hours=2)).isoformat(),
            "description": "Outside office hours",
        }
        invalid = self.client.post(self._student_meeting_requests_url(), invalid_payload, format="json")
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)

    def test_staff_available_slots_returns_slots_for_valid_date(self):
        self._auth(self.staff)
        date_str = self.meeting_datetime.date().isoformat()
        resp = self.client.get(self._available_slots_url(self.staff.id, date_str))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("slots", resp.data)

    def test_staff_available_slots_rejects_invalid_date(self):
        self._auth(self.staff)
        resp = self.client.get(self._available_slots_url(self.staff.id, "2026-99-99"))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", resp.data)

    def test_staff_available_slots_requires_date_query_param(self):
        self._auth(self.staff)
        resp = self.client.get(self._available_slots_url(self.staff.id))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", resp.data)

    def test_staff_available_slots_returns_empty_without_office_hours(self):
        self._auth(self.staff)
        date_str = self.meeting_datetime.date().isoformat()
        resp = self.client.get(self._available_slots_url(self.staff2.id, date_str))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["slots"], [])

    def test_office_hours_delete_invalid_id_and_permission(self):
        self._auth(self.staff)
        # Try deleting non-existent office hours
        resp = self.client.delete(f"{self._office_hours_url()}99999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        # Try deleting as non-staff
        self._auth(self.student)
        office_hours_id = OfficeHours.objects.filter(staff=self.staff).first().id
        resp = self.client.delete(f"{self._office_hours_url()}{office_hours_id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_office_hours_create_missing_fields(self):
        self._auth(self.staff)
        # Missing required fields
        resp = self.client.post(self._office_hours_url(), {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("day_of_week", resp.data)

    def test_meeting_request_create_missing_fields(self):
        self._auth(self.student)
        # Missing required fields
        resp = self.client.post(self._student_meeting_requests_url(), {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("staff", resp.data)

    def test_meeting_request_create_invalid_staff(self):
        self._auth(self.student)
        # Non-existent staff
        payload = {
            "staff": 99999,
            "meeting_datetime": self.meeting_datetime.isoformat(),
            "description": "Invalid staff",
        }
        resp = self.client.post(self._student_meeting_requests_url(), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_method_restrictions_and_permissions(self):
        # POST to meeting_request_list (should be 405)
        self._auth(self.staff)
        resp = self.client.post(self._meeting_requests_url())
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # GET to office_hours_delete (should be 405)
        resp = self.client.get(f"{self._office_hours_url()}99999/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # POST to office_hours_delete (should be 405)
        resp = self.client.post(f"{self._office_hours_url()}99999/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # GET to meeting_request_accept (should be 405)
        resp = self.client.get(self._meeting_action_url(self.pending_request.id, "accept"))
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # GET to meeting_request_deny (should be 405)
        resp = self.client.get(self._meeting_action_url(self.pending_request.id, "deny"))
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
