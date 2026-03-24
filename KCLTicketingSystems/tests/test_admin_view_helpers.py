from datetime import timedelta

from django.test import RequestFactory, TestCase
from django.utils import timezone

from ..models.reply import Reply
from ..models.ticket import Ticket
from ..models.user import User
from ..views import admin_views


class AdminViewHelpersTest(TestCase):
    """Unit tests for helper functions in admin_views.py."""

    def setUp(self):
        self.factory = RequestFactory()

        self.admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="testpass123",
            k_number="99999999",
            role=User.Role.ADMIN,
            is_superuser=True,
        )
        self.staff = User.objects.create_user(
            username="staff",
            email="staff@test.com",
            password="testpass123",
            first_name="Staff",
            last_name="Member",
            k_number="22222222",
            role=User.Role.STAFF,
        )
        self.student = User.objects.create_user(
            username="student",
            email="student@test.com",
            password="testpass123",
            first_name="Alice",
            last_name="Learner",
            k_number="11111111",
            role=User.Role.STUDENT,
            department="Informatics",
        )

        self.ticket_pending = Ticket.objects.create(
            user=self.student,
            department="Informatics",
            type_of_issue="Software Issue",
            additional_details="Needs IDE support",
            status=Ticket.Status.PENDING,
            priority=Ticket.Priority.MEDIUM,
        )
        self.ticket_in_progress = Ticket.objects.create(
            user=self.student,
            department="Engineering",
            type_of_issue="Hardware Issue",
            additional_details="Laptop fan failure",
            status=Ticket.Status.IN_PROGRESS,
            priority=Ticket.Priority.HIGH,
            assigned_to=self.staff,
        )
        self.ticket_resolved = Ticket.objects.create(
            user=self.student,
            department="Informatics",
            type_of_issue="Access Issue",
            additional_details="VPN resolved",
            status=Ticket.Status.RESOLVED,
            priority=Ticket.Priority.LOW,
            assigned_to=self.staff,
        )
        self.ticket_closed = Ticket.objects.create(
            user=self.student,
            department="Medicine",
            type_of_issue="Database Issue",
            additional_details="Case closed",
            status=Ticket.Status.CLOSED,
            priority=Ticket.Priority.URGENT,
            closed_by=self.admin,
        )

    def test_get_ticket_stats_returns_expected_counts(self):
        stats = admin_views._get_ticket_stats()

        self.assertEqual(stats["total_tickets"], 4)
        self.assertEqual(stats["pending_tickets"], 1)
        self.assertEqual(stats["in_progress_tickets"], 1)
        self.assertEqual(stats["resolved_tickets"], 1)
        self.assertEqual(stats["closed_tickets"], 1)

    def test_get_user_stats_returns_expected_counts(self):
        stats = admin_views._get_user_stats()

        self.assertEqual(stats["total_users"], 3)
        self.assertEqual(stats["total_students"], 1)
        self.assertEqual(stats["total_staff"], 1)
        self.assertEqual(stats["total_admins"], 1)

    def test_get_recent_tickets_limits_to_last_7_days(self):
        now = timezone.now()
        Ticket.objects.filter(id=self.ticket_pending.id).update(created_at=now - timedelta(days=2))
        Ticket.objects.filter(id=self.ticket_in_progress.id).update(created_at=now - timedelta(days=6))
        Ticket.objects.filter(id=self.ticket_resolved.id).update(created_at=now - timedelta(days=8))

        recent = list(admin_views._get_recent_tickets())
        recent_ids = [t.id for t in recent]

        self.assertIn(self.ticket_pending.id, recent_ids)
        self.assertIn(self.ticket_in_progress.id, recent_ids)
        self.assertNotIn(self.ticket_resolved.id, recent_ids)

    def test_apply_ticket_search_filters_by_user_name_and_issue(self):
        tickets = Ticket.objects.all()

        by_name = admin_views._apply_ticket_search(tickets, "Alice")
        by_issue = admin_views._apply_ticket_search(tickets, "Hardware")

        self.assertEqual(by_name.count(), 4)
        self.assertEqual(by_issue.count(), 1)
        self.assertEqual(by_issue.first().id, self.ticket_in_progress.id)

    def test_apply_ticket_search_without_value_returns_original_queryset(self):
        tickets = Ticket.objects.all()

        filtered = admin_views._apply_ticket_search(tickets, "")

        self.assertEqual(filtered.count(), tickets.count())

    def test_apply_status_priority_filters_applies_both_filters(self):
        request = self.factory.get("/", {"status": Ticket.Status.IN_PROGRESS, "priority": Ticket.Priority.HIGH})
        filtered = admin_views._apply_status_priority_filters(Ticket.objects.all(), request)

        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().id, self.ticket_in_progress.id)

    def test_apply_department_assignment_filters_handles_unassigned(self):
        request = self.factory.get("/", {"department": "Informatics", "assigned_to": "unassigned"})
        filtered = admin_views._apply_department_assignment_filters(Ticket.objects.all(), request)

        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().id, self.ticket_pending.id)

    def test_apply_department_assignment_filters_handles_specific_assignee(self):
        request = self.factory.get("/", {"assigned_to": str(self.staff.id)})
        filtered = admin_views._apply_department_assignment_filters(Ticket.objects.all(), request)

        self.assertEqual(filtered.count(), 2)

    def test_apply_ticket_filters_combines_all_filter_types(self):
        request = self.factory.get(
            "/",
            {
                "status": Ticket.Status.RESOLVED,
                "priority": Ticket.Priority.LOW,
                "department": "Informatics",
                "assigned_to": str(self.staff.id),
            },
        )
        filtered = admin_views._apply_ticket_filters(Ticket.objects.all(), request)

        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().id, self.ticket_resolved.id)

    def test_paginate_tickets_returns_expected_shape_and_page(self):
        request = self.factory.get("/", {"page": 2, "page_size": 2})
        tickets = Ticket.objects.order_by("id")

        payload = admin_views._paginate_tickets(tickets, request)

        self.assertEqual(payload["total"], 4)
        self.assertEqual(payload["page"], 2)
        self.assertEqual(payload["page_size"], 2)
        self.assertEqual(payload["total_pages"], 2)
        self.assertEqual(len(payload["tickets"]), 2)

    def test_apply_user_search_filters_expected_fields(self):
        users = User.objects.all()

        by_k_number = admin_views._apply_user_search(users, "11111111")
        by_username = admin_views._apply_user_search(users, "staff")

        self.assertEqual(by_k_number.count(), 1)
        self.assertEqual(by_k_number.first().id, self.student.id)
        self.assertEqual(by_username.count(), 1)
        self.assertEqual(by_username.first().id, self.staff.id)

    def test_paginate_users_returns_expected_shape_and_page(self):
        extra_user = User.objects.create_user(
            username="student2",
            email="student2@test.com",
            password="testpass123",
            k_number="33333333",
            role=User.Role.STUDENT,
        )
        request = self.factory.get("/", {"page": 2, "page_size": 2})
        users = User.objects.order_by("id")

        payload = admin_views._paginate_users(users, request)

        self.assertEqual(payload["total"], 4)
        self.assertEqual(payload["page"], 2)
        self.assertEqual(payload["page_size"], 2)
        self.assertEqual(payload["total_pages"], 2)
        self.assertEqual(len(payload["users"]), 2)
        self.assertTrue(any(u["id"] == extra_user.id for u in payload["users"]))

    def test_update_user_fields_updates_only_provided_values(self):
        data = {
            "role": User.Role.STAFF,
            "department": "Engineering",
            "first_name": "Alicia",
            "last_name": "Student",
            "email": "alicia@test.com",
            "is_active": False,
        }

        admin_views._update_user_fields(self.student, data)
        self.student.save()
        self.student.refresh_from_db()

        self.assertEqual(self.student.role, User.Role.STAFF)
        self.assertEqual(self.student.department, "Engineering")
        self.assertEqual(self.student.first_name, "Alicia")
        self.assertEqual(self.student.last_name, "Student")
        self.assertEqual(self.student.email, "alicia@test.com")
        self.assertFalse(self.student.is_active)

    def test_compute_dept_response_times_uses_first_staff_reply_and_skips_negative(self):
        now = timezone.now()

        # Ticket 1: first valid staff reply at +2h (student reply should be ignored).
        Ticket.objects.filter(id=self.ticket_pending.id).update(created_at=now - timedelta(hours=6))
        self.ticket_pending.refresh_from_db()

        Reply.objects.create(user=self.student, ticket=self.ticket_pending, body="Student follow-up")
        r1 = Reply.objects.create(user=self.staff, ticket=self.ticket_pending, body="Staff reply one")
        Reply.objects.filter(id=r1.id).update(created_at=self.ticket_pending.created_at + timedelta(hours=2))
        r2 = Reply.objects.create(user=self.admin, ticket=self.ticket_pending, body="Admin reply")
        Reply.objects.filter(id=r2.id).update(created_at=self.ticket_pending.created_at + timedelta(hours=3))

        # Ticket 2 in same dept: first valid staff reply at +4h.
        Ticket.objects.filter(id=self.ticket_resolved.id).update(created_at=now - timedelta(hours=8))
        self.ticket_resolved.refresh_from_db()
        r3 = Reply.objects.create(user=self.staff, ticket=self.ticket_resolved, body="Staff reply two")
        Reply.objects.filter(id=r3.id).update(created_at=self.ticket_resolved.created_at + timedelta(hours=4))

        # Ticket 3: negative delta should be skipped.
        Ticket.objects.filter(id=self.ticket_closed.id).update(created_at=now - timedelta(hours=1))
        self.ticket_closed.refresh_from_db()
        r4 = Reply.objects.create(user=self.staff, ticket=self.ticket_closed, body="Invalid earlier reply")
        Reply.objects.filter(id=r4.id).update(created_at=self.ticket_closed.created_at - timedelta(minutes=10))

        result = admin_views._compute_dept_response_times(Ticket.objects.filter(id__in=[
            self.ticket_pending.id,
            self.ticket_resolved.id,
            self.ticket_closed.id,
        ]))

        # Informatics average: (2h + 4h) / 2 = 3h
        self.assertAlmostEqual(result.get("Informatics"), 3.0, delta=0.01)
        # Medicine should be absent because the only reply had a negative delta.
        self.assertNotIn("Medicine", result)
