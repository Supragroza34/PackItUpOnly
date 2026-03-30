"""
Staff selection helpers for assigning tickets by department load.

Used by tests and legacy assignment logic; mirrors queryset patterns in serializers.
"""
from ..models import User, Ticket


def get_staff_with_least_tickets_in_department(department):
    """Return one staff dict in ``department`` with the fewest open assignments."""
    staff = get_staff_from_department(department)
    staff_map = map_number_of_tickets_staff(staff)
    ticket_nums = staff_map.keys()
    smallest_num = min(ticket_nums)
    return staff_map.get(smallest_num)

def map_number_of_tickets_staff(staff_members):
    """Map ticket count -> staff row dict for each member in ``staff_members``."""
    staff_map = {}
    for member in staff_members:
        number_of_tickets = get_number_of_tickets_assigned_to_staff(member["id"])
        staff_map[number_of_tickets] = member
    return staff_map      

def get_staff_from_department(department):
    """Queryset values() for staff/admin users in the given department."""
    staff_in_department = User.objects.filter(role__in=[User.Role.STAFF, User.Role.ADMIN], department=department).values(
            'id', 'username', 'first_name', 'last_name', 'email', 'role', 'department',
        )
    return staff_in_department

def get_number_of_tickets_assigned_to_staff(staff_id):
    """Count tickets currently assigned to ``staff_id``."""
    number_of_tickets = Ticket.objects.filter(assigned_to=staff_id).count()
    return number_of_tickets