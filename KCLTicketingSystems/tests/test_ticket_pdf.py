"""
Tests for the PDF ticket summary feature.

Covers:
- ticket_pdf view: auth, ownership, closed-status gate, response format
- _build_pdf: all reply role branches, no-reply, legacy ticket, edge cases
- _format_datetime: None, aware, naive
- _user_display_name: None, full name, username fallback
"""
from datetime import datetime

from django.test import TestCase
from django.utils import timezone as tz
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from ..models.ticket import Ticket
from ..models.reply import Reply
from ..models.user import User
from ..views.ticket_pdf_view import _build_pdf, _format_datetime, _user_display_name, _pdf_safe_text


# ---------------------------------------------------------------------------
# Module-level fixture helpers (keep setUp methods short)
# ---------------------------------------------------------------------------

def _make_student(username, email, first='John', last='Doe'):
    """Support the ticket PDF tests by make student so assertions remain focused on outcomes."""
    return User.objects.create_user(
        username=username, email=email, password='Pass123!',
        first_name=first, last_name=last, role=User.Role.STUDENT,
    )


def _make_staff(username, email):
    """Support the ticket PDF tests by make staff so assertions remain focused on outcomes."""
    return User.objects.create_user(
        username=username, email=email, password='Pass123!',
        first_name='Jane', last_name='Dee', role=User.Role.STAFF,
    )


def _make_closed_ticket(user, **kwargs):
    """Support the ticket PDF tests by make closed ticket so assertions remain focused on outcomes."""
    return Ticket.objects.create(
        user=user, department='Informatics', type_of_issue='Login Issue',
        additional_details='Cannot log in to portal',
        status=Ticket.Status.CLOSED, **kwargs,
    )


def _make_ticket(user, ticket_status):
    """Support the ticket PDF tests by make ticket so assertions remain focused on outcomes."""
    return Ticket.objects.create(
        user=user, department='IT', type_of_issue='General',
        additional_details='Some details', status=ticket_status,
    )


# ===========================================================================
# View endpoint tests
# ===========================================================================

class TicketPdfAuthTests(APITestCase):
    """Auth and access-control checks for GET /api/tickets/<id>/pdf/. This keeps regressions visible early in the release cycle."""

    def setUp(self):
        """Establish shared fixtures so tests stay focused on behavior rather than setup details."""
        self.client = APIClient()
        self.student = _make_student('stu1', 'stu1@kcl.ac.uk')
        self.other = _make_student('stu2', 'stu2@kcl.ac.uk')
        self.ticket = _make_closed_ticket(self.student)

    def _url(self, ticket_id):
        """Support the ticket PDF tests by url so assertions remain focused on outcomes."""
        return f'/api/tickets/{ticket_id}/pdf/'

    def test_unauthenticated_returns_401(self):
        """Guard unauthenticated returns 401 in the ticket PDF flow so regressions surface early."""
        response = self.client.get(self._url(self.ticket.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_nonexistent_ticket_returns_404(self):
        """Guard nonexistent ticket returns 404 in the ticket PDF flow so regressions surface early."""
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self._url(99999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_wrong_owner_returns_403(self):
        """Guard wrong owner returns 403 in the ticket PDF flow so regressions surface early."""
        self.client.force_authenticate(user=self.other)
        response = self.client.get(self._url(self.ticket.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_wrong_owner_error_message(self):
        """Guard wrong owner error message in the ticket PDF flow so regressions surface early."""
        self.client.force_authenticate(user=self.other)
        response = self.client.get(self._url(self.ticket.id))
        self.assertIn('permission', response.data['detail'].lower())


class TicketPdfStatusGateTests(APITestCase):
    """Gate: PDF only available once ticket is closed. This keeps regressions visible early in the release cycle."""

    def setUp(self):
        """Establish shared fixtures so tests stay focused on behavior rather than setup details."""
        self.client = APIClient()
        self.student = _make_student('stu3', 'stu3@kcl.ac.uk')

    def _get_pdf(self, ticket_status):
        """Support the ticket PDF tests by get PDF so assertions remain focused on outcomes."""
        ticket = _make_ticket(self.student, ticket_status)
        self.client.force_authenticate(user=self.student)
        return self.client.get(f'/api/tickets/{ticket.id}/pdf/')

    def test_pending_ticket_returns_403(self):
        """Guard pending ticket returns 403 in the ticket PDF flow so regressions surface early."""
        response = self._get_pdf(Ticket.Status.PENDING)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_in_progress_ticket_returns_403(self):
        """Guard in progress ticket returns 403 in the ticket PDF flow so regressions surface early."""
        response = self._get_pdf(Ticket.Status.IN_PROGRESS)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_resolved_ticket_returns_403(self):
        """Guard resolved ticket returns 403 in the ticket PDF flow so regressions surface early."""
        response = self._get_pdf(Ticket.Status.RESOLVED)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_not_closed_error_message(self):
        """Guard not closed error message in the ticket PDF flow so regressions surface early."""
        ticket = _make_ticket(self.student, Ticket.Status.PENDING)
        self.client.force_authenticate(user=self.student)
        response = self.client.get(f'/api/tickets/{ticket.id}/pdf/')
        self.assertIn('closed', response.data['detail'].lower())

    def test_closed_ticket_returns_200(self):
        """Guard closed ticket returns 200 in the ticket PDF flow so regressions surface early."""
        response = self._get_pdf(Ticket.Status.CLOSED)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TicketPdfResponseFormatTests(APITestCase):
    """Response format checks: content-type, disposition, body. This keeps regressions visible early in the release cycle."""

    def setUp(self):
        """Establish shared fixtures so tests stay focused on behavior rather than setup details."""
        self.client = APIClient()
        self.student = _make_student('stu4', 'stu4@kcl.ac.uk')
        self.ticket = _make_closed_ticket(self.student)
        self.client.force_authenticate(user=self.student)
        self.response = self.client.get(f'/api/tickets/{self.ticket.id}/pdf/')

    def test_content_type_is_pdf(self):
        """Guard content type is PDF in the ticket PDF flow so regressions surface early."""
        self.assertEqual(self.response['Content-Type'], 'application/pdf')

    def test_content_disposition_filename(self):
        """Guard content disposition filename in the ticket PDF flow so regressions surface early."""
        expected = f'attachment; filename="ticket_{self.ticket.id}_summary.pdf"'
        self.assertEqual(self.response['Content-Disposition'], expected)

    def test_response_body_is_non_empty(self):
        """Guard response body is non empty in the ticket PDF flow so regressions surface early."""
        self.assertGreater(len(self.response.content), 0)

    def test_response_body_starts_with_pdf_magic_bytes(self):
        """Guard response body starts with PDF magic bytes in the ticket PDF flow so regressions surface early."""
        self.assertTrue(self.response.content.startswith(b'%PDF'))


class TicketPdfRichTextRegressionTests(APITestCase):
    """Regression tests for rich-text additional_details in PDF generation. This keeps regressions visible early in the release cycle."""

    def setUp(self):
        """Establish shared fixtures so tests stay focused on behavior rather than setup details."""
        self.client = APIClient()
        self.student = _make_student('stu_rich', 'stu_rich@kcl.ac.uk')
        self.ticket = Ticket.objects.create(
            user=self.student,
            department='Informatics',
            type_of_issue='Software Installation Issues',
            status=Ticket.Status.CLOSED,
            additional_details=(
                '<p data-indent="1">Line 1 <strong>bold</strong><br />'
                'Line 2 &amp; symbols <script>alert(1)</script></p>'
            ),
        )
        self.client.force_authenticate(user=self.student)

    def test_download_pdf_succeeds_with_rich_text_details(self):
        """Guard download PDF succeeds with rich text details in the ticket PDF flow so regressions surface early."""
        response = self.client.get(f'/api/tickets/{self.ticket.id}/pdf/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF'))


# ===========================================================================
# _build_pdf content/branch tests
# ===========================================================================

class TicketPdfBuildTests(TestCase):
    """Directly tests _build_pdf across all reply-role and edge-case branches. This keeps regressions visible early in the release cycle."""

    def setUp(self):
        """Establish shared fixtures so tests stay focused on behavior rather than setup details."""
        self.student = _make_student('bs1', 'bs1@kcl.ac.uk')
        self.staff = _make_staff('bs2', 'bs2@kcl.ac.uk')
        self.ticket = _make_closed_ticket(self.student)

    def _pdf(self, ticket=None):
        """Support the ticket PDF tests by PDF so assertions remain focused on outcomes."""
        return _build_pdf(ticket or self.ticket)

    def test_returns_bytes(self):
        """Guard returns bytes in the ticket PDF flow so regressions surface early."""
        self.assertIsInstance(self._pdf(), bytes)

    def test_starts_with_pdf_magic_bytes(self):
        """Guard starts with PDF magic bytes in the ticket PDF flow so regressions surface early."""
        self.assertTrue(self._pdf().startswith(b'%PDF'))

    def test_with_no_replies(self):
        """Guard with no replies in the ticket PDF flow so regressions surface early."""
        result = self._pdf()
        self.assertGreater(len(result), 1000)

    def test_with_student_reply(self):
        """Guard with student reply in the ticket PDF flow so regressions surface early."""
        Reply.objects.create(user=self.student, ticket=self.ticket, body='My query')
        self.assertTrue(self._pdf().startswith(b'%PDF'))

    def test_with_staff_reply(self):
        """Guard with staff reply in the ticket PDF flow so regressions surface early."""
        Reply.objects.create(user=self.staff, ticket=self.ticket, body='Staff reply')
        self.assertTrue(self._pdf().startswith(b'%PDF'))

    def test_with_admin_reply(self):
        """Guard with admin reply in the ticket PDF flow so regressions surface early."""
        admin = User.objects.create_user(
            username='adm', email='adm@kcl.ac.uk', password='x', role=User.Role.ADMIN,
        )
        Reply.objects.create(user=admin, ticket=self.ticket, body='Admin reply')
        self.assertTrue(self._pdf().startswith(b'%PDF'))

    def test_with_multiple_replies(self):
        """Guard with multiple replies in the ticket PDF flow so regressions surface early."""
        Reply.objects.create(user=self.student, ticket=self.ticket, body='First')
        Reply.objects.create(user=self.staff, ticket=self.ticket, body='Second')
        self.assertTrue(self._pdf().startswith(b'%PDF'))

    def test_with_assigned_to_and_closed_by(self):
        """Guard with assigned to and closed by in the ticket PDF flow so regressions surface early."""
        self.ticket.assigned_to = self.staff
        self.ticket.closed_by = self.student
        self.ticket.save()
        self.assertTrue(self._pdf().startswith(b'%PDF'))

    def test_legacy_ticket_without_user(self):
        """Guard legacy ticket without user in the ticket PDF flow so regressions surface early."""
        ticket = Ticket.objects.create(
            user=None, name='Legacy', surname='User', department='IT',
            type_of_issue='Old Issue', additional_details='Old details',
            status=Ticket.Status.CLOSED,
        )
        self.assertTrue(self._pdf(ticket).startswith(b'%PDF'))

    def test_ticket_with_empty_additional_details(self):
        """Guard ticket with empty additional details in the ticket PDF flow so regressions surface early."""
        self.ticket.additional_details = ''
        self.ticket.save()
        self.assertTrue(self._pdf().startswith(b'%PDF'))

    def test_ticket_with_no_assigned_or_closed_by(self):
        """Guard ticket with no assigned or closed by in the ticket PDF flow so regressions surface early."""
        self.ticket.assigned_to = None
        self.ticket.closed_by = None
        self.ticket.save()
        self.assertTrue(self._pdf().startswith(b'%PDF'))

    def test_user_with_no_first_last_name_uses_username(self):
        """Guard user with no first last name uses username in the ticket PDF flow so regressions surface early."""
        user = User.objects.create_user(
            username='onlyusername', email='o@kcl.ac.uk', password='x',
            first_name='', last_name='', role=User.Role.STUDENT,
        )
        ticket = _make_closed_ticket(user)
        self.assertTrue(self._pdf(ticket).startswith(b'%PDF'))


# ===========================================================================
# _format_datetime unit tests
# ===========================================================================

class FormatDatetimeTests(TestCase):
    """Unit tests for _format_datetime helper. This keeps regressions visible early in the release cycle."""

    def test_none_returns_unknown(self):
        """Guard none returns unknown in the ticket PDF flow so regressions surface early."""
        self.assertEqual(_format_datetime(None), 'Unknown')

    def test_naive_datetime_formatted(self):
        """Guard naive datetime formatted in the ticket PDF flow so regressions surface early."""
        dt = datetime(2025, 6, 1, 10, 0)
        result = _format_datetime(dt)
        self.assertIn('June', result)
        self.assertIn('2025', result)

    def test_aware_datetime_formatted(self):
        """Guard aware datetime formatted in the ticket PDF flow so regressions surface early."""
        dt = tz.make_aware(datetime(2025, 3, 15, 14, 30))
        result = _format_datetime(dt)
        self.assertIn('2025', result)
        self.assertIn('March', result)

    def test_format_includes_utc_label(self):
        """Guard format includes utc label in the ticket PDF flow so regressions surface early."""
        dt = datetime(2025, 1, 20, 9, 0)
        self.assertIn('UTC', _format_datetime(dt))

    def test_format_includes_time(self):
        """Guard format includes time in the ticket PDF flow so regressions surface early."""
        dt = datetime(2025, 1, 20, 9, 5)
        result = _format_datetime(dt)
        self.assertIn('09:05', result)


# ===========================================================================
# _user_display_name unit tests
# ===========================================================================

class UserDisplayNameTests(TestCase):
    """Unit tests for _user_display_name helper. This keeps regressions visible early in the release cycle."""

    def test_none_returns_unknown(self):
        """Guard none returns unknown in the ticket PDF flow so regressions surface early."""
        self.assertEqual(_user_display_name(None), 'Unknown')

    def test_user_with_full_name(self):
        """Guard user with full name in the ticket PDF flow so regressions surface early."""
        user = User.objects.create_user(
            username='jdoe', email='jd@kcl.ac.uk', password='x',
            first_name='John', last_name='Doe',
        )
        self.assertEqual(_user_display_name(user), 'John Doe')

    def test_user_with_no_name_falls_back_to_username(self):
        """Guard user with no name falls back to username in the ticket PDF flow so regressions surface early."""
        user = User.objects.create_user(
            username='myusername', email='mu@kcl.ac.uk', password='x',
            first_name='', last_name='',
        )
        self.assertEqual(_user_display_name(user), 'myusername')

    def test_user_with_only_first_name(self):
        """Guard user with only first name in the ticket PDF flow so regressions surface early."""
        user = User.objects.create_user(
            username='fn', email='fn@kcl.ac.uk', password='x',
            first_name='Alice', last_name='',
        )
        self.assertEqual(_user_display_name(user), 'Alice')

    def test_user_with_only_last_name(self):
        """Guard user with only last name in the ticket PDF flow so regressions surface early."""
        user = User.objects.create_user(
            username='ln', email='ln@kcl.ac.uk', password='x',
            first_name='', last_name='Smith',
        )
        self.assertEqual(_user_display_name(user), 'Smith')


class PdfSafeTextTests(TestCase):
    """Unit tests for _pdf_safe_text helper. This keeps regressions visible early in the release cycle."""

    def test_none_returns_empty_string(self):
        """Guard none returns empty string in the ticket PDF flow so regressions surface early."""
        self.assertEqual(_pdf_safe_text(None), '')

    def test_html_is_converted_to_safe_text_with_breaks(self):
        """Guard html is converted to safe text with breaks in the ticket PDF flow so regressions surface early."""
        text = _pdf_safe_text('<p>Hello <strong>World</strong><br/>A &amp; B</p>')
        self.assertIn('Hello World', text)
        self.assertIn('A &amp; B', text)
        self.assertIn('<br/>', text)
