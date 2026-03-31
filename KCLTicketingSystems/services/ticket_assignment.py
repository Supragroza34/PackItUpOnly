"""Service helpers for ticket assignment and creation workflows."""

from django.db.models import Count

from ..models.ticket import Ticket
from ..models.user import User


def select_least_loaded_staff_in_department(department):
    """Return staff/admin user in ``department`` with the fewest assigned tickets."""
    return (
        User.objects.filter(role__in=[User.Role.STAFF, User.Role.ADMIN], department=department)
        .annotate(ticket_count=Count("assigned_tickets"))
        .order_by("ticket_count")
        .first()
    )


def create_ticket_with_department_assignment(validated_data):
    """Create a ticket and auto-assign to least-loaded department staff/admin."""
    department = validated_data.get("department")
    validated_data["assigned_to"] = select_least_loaded_staff_in_department(department)
    return Ticket.objects.create(**validated_data)
