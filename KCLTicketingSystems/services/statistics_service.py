"""Statistics and analytics helpers for admin reporting endpoints."""

from collections import defaultdict

from django.db.models import Q, Count, Avg, F, ExpressionWrapper, DurationField

from ..models.ticket import Ticket
from ..models.reply import Reply
from ..models.user import User


def compute_dept_response_times(tickets):
    """Map department -> average first staff/admin response time in hours."""
    first_reply = _first_staff_reply_map(tickets)
    ticket_meta = _ticket_meta_map(tickets)
    return _dept_response_time_hours(first_reply, ticket_meta)


def _first_staff_reply_map(tickets):
    staff_roles = [User.Role.STAFF, User.Role.ADMIN]
    first_reply = {}
    rows = Reply.objects.filter(ticket__in=tickets, user__role__in=staff_roles)
    for reply in rows.order_by("created_at").values("ticket_id", "created_at"):
        ticket_id = reply["ticket_id"]
        if ticket_id not in first_reply:
            first_reply[ticket_id] = reply["created_at"]
    return first_reply


def _ticket_meta_map(tickets):
    return {
        ticket_id: (department, created_at)
        for ticket_id, department, created_at in tickets.values_list("id", "department", "created_at")
    }


def _dept_response_time_hours(first_reply, ticket_meta):
    dept_times = defaultdict(list)
    for ticket_id, first_reply_at in first_reply.items():
        meta = ticket_meta.get(ticket_id)
        if not meta:
            continue
        department, created_at = meta
        if not (department and created_at):
            continue
        delta = (first_reply_at - created_at).total_seconds()
        if delta < 0:
            continue
        dept_times[department].append(delta)
    return {dept: round((sum(times) / len(times)) / 3600, 2) for dept, times in dept_times.items()}


def ticket_department_stats_annotations():
    """Return common annotations used by department statistics reports."""
    return {
        "total_tickets": Count("id"),
        "pending": Count("id", filter=Q(status=Ticket.Status.PENDING)),
        "in_progress": Count("id", filter=Q(status=Ticket.Status.IN_PROGRESS)),
        "resolved": Count("id", filter=Q(status=Ticket.Status.RESOLVED)),
        "closed": Count("id", filter=Q(status=Ticket.Status.CLOSED)),
        "low": Count("id", filter=Q(priority=Ticket.Priority.LOW)),
        "medium": Count("id", filter=Q(priority=Ticket.Priority.MEDIUM)),
        "high": Count("id", filter=Q(priority=Ticket.Priority.HIGH)),
        "urgent": Count("id", filter=Q(priority=Ticket.Priority.URGENT)),
        "avg_resolution_seconds": Avg(
            ExpressionWrapper(F("updated_at") - F("created_at"), output_field=DurationField()),
            filter=Q(status=Ticket.Status.CLOSED, updated_at__isnull=False),
        ),
    }


def ticket_department_stats_queryset(tickets):
    """Aggregate department-level counts and averages ordered by total tickets."""
    return tickets.values("department").annotate(**ticket_department_stats_annotations()).order_by("-total_tickets")


def format_department_statistics(department_stats, dept_response_times):
    """Shape department stats into API/CSV-friendly dicts."""
    return [_format_department_stat_row(stat, dept_response_times) for stat in department_stats]


def _format_department_stat_row(stat, dept_response_times):
    department = stat["department"]
    return {
        "department": department,
        "total_tickets": stat["total_tickets"],
        "status_breakdown": _status_breakdown(stat),
        "priority_breakdown": _priority_breakdown(stat),
        "avg_resolution_time_hours": _avg_resolution_hours(stat),
        "avg_response_time_hours": dept_response_times.get(department),
    }


def _status_breakdown(stat):
    return {
        "pending": stat["pending"],
        "in_progress": stat["in_progress"],
        "resolved": stat["resolved"],
        "closed": stat["closed"],
    }


def _priority_breakdown(stat):
    return {
        "low": stat["low"],
        "medium": stat["medium"],
        "high": stat["high"],
        "urgent": stat["urgent"],
    }


def _avg_resolution_hours(stat):
    duration = stat["avg_resolution_seconds"]
    if not duration:
        return None
    return round(duration.total_seconds() / 3600, 2)
