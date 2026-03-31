"""Admin REST API: dashboard metrics, ticket and user CRUD, staff listing, and CSV exports."""

import logging
from datetime import timedelta, datetime
import csv

from django.db.models import Q
from django.utils import timezone
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from ..models.ticket import Ticket
from ..models.user import User
from ..serializers import (
    TicketSerializer, 
    TicketListSerializer, 
    TicketUpdateSerializer,
    UserSerializer,
    DashboardStatsSerializer
)
from ..permissions import IsAdmin
from ..services import statistics_service

from ..utils import notify_on_ticket_update, auto_close_stale_awaiting_response

logger = logging.getLogger(__name__)


# ================= DASHBOARD STATISTICS =================

def _get_ticket_stats():
    """Get ticket statistics."""
    return {
        'total_tickets': Ticket.objects.count(),
        'pending_tickets': Ticket.objects.filter(status=Ticket.Status.PENDING).count(),
        'in_progress_tickets': Ticket.objects.filter(status=Ticket.Status.IN_PROGRESS).count(),
        'resolved_tickets': Ticket.objects.filter(status=Ticket.Status.RESOLVED).count(),
        'closed_tickets': Ticket.objects.filter(status=Ticket.Status.CLOSED).count(),
    }


def _get_user_stats():
    """Get user statistics."""
    return {
        'total_users': User.objects.count(),
        'total_students': User.objects.filter(role=User.Role.STUDENT).count(),
        'total_staff': User.objects.filter(role=User.Role.STAFF).count(),
        'total_admins': User.objects.filter(role=User.Role.ADMIN).count(),
    }


def _get_recent_tickets():
    """Get recent tickets from last 7 days."""
    week_ago = timezone.now() - timedelta(days=7)
    return Ticket.objects.select_related('user', 'closed_by').filter(created_at__gte=week_ago).order_by('-created_at')[:10]


def _compute_dept_response_times(tickets):
    """Compatibility wrapper for tests; delegates to the statistics service."""
    return statistics_service.compute_dept_response_times(tickets)


def _first_staff_reply_map(tickets):
    """Compatibility wrapper for tests; delegates to the statistics service."""
    return statistics_service._first_staff_reply_map(tickets)


def _ticket_meta_map(tickets):
    """Compatibility wrapper for tests; delegates to the statistics service."""
    return statistics_service._ticket_meta_map(tickets)


def _dept_response_time_hours(first_reply, ticket_meta):
    """Compatibility wrapper for tests; delegates to the statistics service."""
    return statistics_service._dept_response_time_hours(first_reply, ticket_meta)


def _internal_error_response(exc):
    """Log internal exception details and return a generic API error payload."""
    logger.exception("Admin API internal error: %s", exc)
    return Response({"error": "An internal server error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _internal_error_http_response(exc):
    """Log internal exception details and return a generic plain-text error response."""
    logger.exception("Admin export internal error: %s", exc)
    return HttpResponse("Error: An internal server error occurred.", status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def dashboard_stats(request):
    """Get dashboard statistics"""
    try:
        auto_close_stale_awaiting_response()
        payload = _dashboard_stats_payload()
        return Response(DashboardStatsSerializer(payload).data)
    except Exception as exc:
        return _internal_error_response(exc)


def _dashboard_stats_payload():
    payload = {}
    payload.update(_dashboard_ticket_counts())
    payload.update(_dashboard_user_counts())
    payload["recent_tickets"] = _recent_dashboard_tickets()
    return payload


def _dashboard_ticket_counts():
    return {
        "total_tickets": Ticket.objects.count(),
        "pending_tickets": Ticket.objects.filter(status=Ticket.Status.PENDING).count(),
        "in_progress_tickets": Ticket.objects.filter(status=Ticket.Status.IN_PROGRESS).count(),
        "resolved_tickets": Ticket.objects.filter(status=Ticket.Status.RESOLVED).count(),
        "closed_tickets": Ticket.objects.filter(status=Ticket.Status.CLOSED).count(),
    }


def _dashboard_user_counts():
    return {
        "total_users": User.objects.count(),
        "total_students": User.objects.filter(role=User.Role.STUDENT, is_superuser=False).count(),
        "total_staff": User.objects.filter(role=User.Role.STAFF, is_superuser=False).count(),
        "total_admins": User.objects.filter(Q(role=User.Role.ADMIN) | Q(is_superuser=True)).count(),
    }


def _recent_dashboard_tickets():
    week_ago = timezone.now() - timedelta(days=7)
    return Ticket.objects.filter(created_at__gte=week_ago).order_by("-created_at")[:10]


# ================= TICKET MANAGEMENT =================

def _apply_ticket_search(tickets, search):
    """Apply search filter to tickets (user fields via user relation)."""
    if not search:
        return tickets
    return tickets.filter(
        Q(user__first_name__icontains=search) |
        Q(user__last_name__icontains=search) |
        Q(user__k_number__icontains=search) |
        Q(user__email__icontains=search) |
        Q(department__icontains=search) |
        Q(type_of_issue__icontains=search)
    )


def _apply_status_priority_filters(tickets, request):
    """Apply status and priority filters."""
    status_filter = request.GET.get('status')
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    priority_filter = request.GET.get('priority')
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)
    return tickets


def _apply_department_assignment_filters(tickets, request):
    """Apply department and assignment filters."""
    department_filter = request.GET.get('department')
    if department_filter:
        tickets = tickets.filter(department=department_filter)
    assigned_filter = request.GET.get('assigned_to')
    if assigned_filter:
        if assigned_filter == 'unassigned':
            tickets = tickets.filter(assigned_to__isnull=True)
        else:
            tickets = tickets.filter(assigned_to_id=assigned_filter)
    return tickets


def _apply_ticket_filters(tickets, request):
    """Apply status, priority, department, and assignment filters."""
    tickets = _apply_status_priority_filters(tickets, request)
    return _apply_department_assignment_filters(tickets, request)


def _paginate_tickets(tickets, request):
    """Apply pagination and return paginated response data."""
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    start = (page - 1) * page_size
    end = start + page_size
    total_count = tickets.count()
    tickets_page = tickets[start:end]
    serializer = TicketListSerializer(tickets_page, many=True)
    return {
        'tickets': serializer.data,
        'total': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': (total_count + page_size - 1) // page_size
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_tickets_list(request):
    """Get all tickets with filtering, searching, and pagination"""
    try:
        auto_close_stale_awaiting_response()
        tickets = _admin_tickets_queryset(request)
        return Response(_paginate_tickets(tickets, request))
    except Exception as exc:
        return _internal_error_response(exc)


def _admin_tickets_queryset(request):
    """Build and return the filtered ticket queryset for the admin tickets list view."""
    tickets = (
        Ticket.objects.select_related("user", "closed_by")
        .all()
        .order_by("-created_at")
    )
    search = request.GET.get("search", "")
    tickets = _apply_ticket_search(tickets, search)
    return _apply_ticket_filters(tickets, request)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_ticket_detail(request, ticket_id):
    """Get single ticket details"""
    try:
        ticket = Ticket.objects.select_related('user', 'assigned_to', 'closed_by').get(id=ticket_id)
        serializer = TicketSerializer(ticket)
        return Response(serializer.data)
    except Ticket.DoesNotExist:
        return Response({'error': 'Ticket not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as exc:
        return _internal_error_response(exc)


@api_view(['PATCH', 'PUT'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_ticket_update(request, ticket_id):
    """Update ticket (status, priority, assignment, notes)"""
    try:
        return _admin_ticket_update_response(request, ticket_id)
    except Ticket.DoesNotExist:
        return Response({'error': 'Ticket not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as exc:
        return _internal_error_response(exc)


def _set_closed_by_if_needed(ticket, user):
    if ticket.status != Ticket.Status.CLOSED:
        return
    ticket.closed_by = user
    ticket.save(update_fields=["closed_by"])


def _admin_ticket_update_response(request, ticket_id):
    ticket = Ticket.objects.select_related("user", "assigned_to", "closed_by").get(id=ticket_id)
    serializer = TicketUpdateSerializer(ticket, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()
    ticket.refresh_from_db()
    _set_closed_by_if_needed(ticket, request.user)
    ticket.refresh_from_db()
    notify_on_ticket_update(ticket, updated_by=request.user)
    return Response(TicketSerializer(ticket).data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_ticket_delete(request, ticket_id):
    """Delete a ticket"""
    try:
        ticket = Ticket.objects.get(id=ticket_id)
        ticket.delete()
        return Response({'success': True, 'message': 'Ticket deleted successfully'})
    except Ticket.DoesNotExist:
        return Response({'error': 'Ticket not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as exc:
        return _internal_error_response(exc)


# ================= USER MANAGEMENT =================

def _apply_user_search(users, search):
    """Apply search filter to users."""
    if not search:
        return users
    return users.filter(
        Q(username__icontains=search) |
        Q(email__icontains=search) |
        Q(first_name__icontains=search) |
        Q(last_name__icontains=search) |
        Q(k_number__icontains=search)
    )


def _paginate_users(users, request):
    """Apply pagination and return paginated response data."""
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    start = (page - 1) * page_size
    end = start + page_size
    total_count = users.count()
    users_page = users[start:end]
    serializer = UserSerializer(users_page, many=True)
    return {
        'users': serializer.data,
        'total': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': (total_count + page_size - 1) // page_size
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_users_list(request):
    """Get all users with filtering and pagination"""
    try:
        users = User.objects.all().order_by("-date_joined")
        users = _apply_user_search(users, request.GET.get("search", ""))
        users = _apply_users_role_filter(users, request.GET.get("role"))
        return Response(_paginate_users(users, request))
    except Exception as exc:
        return _internal_error_response(exc)


def _apply_users_role_filter(users, role_filter):
    """Filter the users queryset by role; return unfiltered if no role_filter is given."""
    if not role_filter:
        return users
    if role_filter == "admin":
        return users.filter(Q(role=User.Role.ADMIN) | Q(is_superuser=True))
    if role_filter == "student":
        return users.filter(role=User.Role.STUDENT, is_superuser=False)
    if role_filter == "staff":
        return users.filter(role=User.Role.STAFF, is_superuser=False)
    return users.filter(role=role_filter)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_user_detail(request, user_id):
    """Get single user details"""
    try:
        user = User.objects.get(id=user_id)
        serializer = UserSerializer(user)
        return Response(serializer.data)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as exc:
        return _internal_error_response(exc)


def _update_user_fields(user, data):
    """Update user fields from request data."""
    if 'role' in data:
        user.role = data['role']
    if 'department' in data:
        user.department = data['department']
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'email' in data:
        user.email = data['email']
    if 'is_active' in data:
        user.is_active = data['is_active']


@api_view(['PATCH', 'PUT'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_user_update(request, user_id):
    """Update user details (role, department, etc.)"""
    try:
        user = User.objects.get(id=user_id)
        _update_user_fields(user, request.data)
        user.save()
        serializer = UserSerializer(user)
        return Response(serializer.data)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as exc:
        return _internal_error_response(exc)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_user_delete(request, user_id):
    """Delete a user"""
    try:
        user = User.objects.get(id=user_id)
        
        # Prevent deleting self
        if user.id == request.user.id:
            return Response({'error': 'Cannot delete your own account'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.delete()
        return Response({'success': True, 'message': 'User deleted successfully'})
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as exc:
        return _internal_error_response(exc)


# ================= STAFF USERS FOR ASSIGNMENT =================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_staff_list(request):
    """Get list of staff and admin users for ticket assignment (dropdown: staff and admin only)."""
    try:
        staff = User.objects.filter(role__in=[User.Role.STAFF, User.Role.ADMIN]).values(
            'id', 'username', 'first_name', 'last_name', 'email', 'role'
        )
        return Response({'staff': list(staff)})
    except Exception as exc:
        return _internal_error_response(exc)


# ================= STATISTICS AND ANALYTICS =================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def get_ticket_statistics(request):
    """Get detailed ticket statistics by department with date filtering."""
    try:
        parsed = _parse_get_ticket_statistics_date_range(request)
        if isinstance(parsed, Response):
            return parsed

        start_date, end_date = parsed
        tickets = _tickets_for_date_range(start_date, end_date)
        department_stats = _ticket_department_stats_queryset(tickets)
        dept_response_times = _compute_dept_response_times(tickets)
        formatted_stats = _format_department_statistics(department_stats, dept_response_times)
        return Response(
            {
                "date_range": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
                "total_tickets": tickets.count(),
                "department_statistics": formatted_stats,
            }
        )
    except Exception as exc:
        return _internal_error_response(exc)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def export_statistics_csv(request):
    """Export statistics summary as CSV."""
    try:
        parsed = _parse_export_statistics_csv_date_range(request)
        if isinstance(parsed, HttpResponse):
            return parsed

        start_date, end_date = parsed
        tickets = _tickets_for_date_range(start_date, end_date)
        return _export_statistics_csv_response(tickets, start_date, end_date)
    except Exception as exc:
        return _internal_error_http_response(exc)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def export_tickets_csv(request):
    """Export all individual tickets as CSV."""
    try:
        parsed = _parse_export_tickets_csv_date_range(request)
        if isinstance(parsed, HttpResponse):
            return parsed

        start_date, end_date = parsed
        tickets = _tickets_for_date_range(start_date, end_date, select_related=True)
        return _export_tickets_csv_response(tickets, start_date, end_date)
    except Exception as exc:
        return _internal_error_http_response(exc)


def _tickets_for_date_range(start_date, end_date, select_related=False):
    qs = Ticket.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
    if select_related:
        qs = qs.select_related("user", "assigned_to").order_by("-created_at")
    return qs


def _parse_get_ticket_statistics_date_range(request):
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")
    if start_date_str and end_date_str:
        return _parse_iso_date_range_for_api(start_date_str, end_date_str)
    return _parse_days_date_range_for_api(request.GET.get("days", "30"))


def _parse_iso_date_range_for_api(start_date_str, end_date_str):
    try:
        start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
        end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return Response(
            {"error": "Invalid start_date or end_date format. Expected ISO 8601 format."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return start_date, end_date


def _parse_days_date_range_for_api(days_param):
    try:
        days = int(days_param)
        if days <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return Response(
            {"error": 'Invalid "days" parameter. Must be a positive integer.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    end_date = timezone.now()
    return end_date - timedelta(days=days), end_date


def _ticket_department_stats_annotations():
    """Compatibility wrapper for tests; delegates to the statistics service."""
    return statistics_service.ticket_department_stats_annotations()


def _ticket_department_stats_queryset(tickets):
    """Compatibility wrapper for tests; delegates to the statistics service."""
    return statistics_service.ticket_department_stats_queryset(tickets)


def _format_department_statistics(department_stats, dept_response_times):
    """Compatibility wrapper for tests; delegates to the statistics service."""
    return statistics_service.format_department_statistics(department_stats, dept_response_times)


def _parse_export_statistics_csv_date_range(request):
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")
    if start_date_str and end_date_str:
        try:
            start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
            end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return HttpResponse("Invalid date format. Expected ISO 8601 format.", status=400)
        return start_date, end_date

    days_param = request.GET.get("days", "30")
    try:
        days = int(days_param)
        if days <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return HttpResponse('Invalid "days" parameter. Must be a positive integer.', status=400)
    end_date = timezone.now()
    return end_date - timedelta(days=days), end_date


def _export_statistics_csv_response(tickets, start_date, end_date):
    response = HttpResponse(content_type="text/csv")
    response[
        "Content-Disposition"
    ] = f'attachment; filename="ticket_statistics_{start_date.date()}_to_{end_date.date()}.csv"'
    writer = csv.writer(response)
    writer.writerow(_statistics_csv_header())

    department_stats = _ticket_department_stats_queryset(tickets)
    dept_response_times = _compute_dept_response_times(tickets)
    _write_export_statistics_rows(writer, department_stats, dept_response_times)
    return response


def _statistics_csv_header():
    return [
        "Department",
        "Total Tickets",
        "Pending",
        "In Progress",
        "Resolved",
        "Closed",
        "Low Priority",
        "Medium Priority",
        "High Priority",
        "Urgent Priority",
        "Avg Resolution Time (hours)",
        "Avg Response Time (hours)",
    ]


def _write_export_statistics_rows(writer, department_stats, dept_response_times):
    for stat in department_stats:
        dept = stat["department"]
        avg_resolution_hours = (
            round(stat["avg_resolution_seconds"].total_seconds() / 3600, 2)
            if stat["avg_resolution_seconds"]
            else ""
        )
        avg_response_hours = dept_response_times.get(dept, "")
        writer.writerow(
            [
                dept,
                stat["total_tickets"],
                stat["pending"],
                stat["in_progress"],
                stat["resolved"],
                stat["closed"],
                stat["low"],
                stat["medium"],
                stat["high"],
                stat["urgent"],
                avg_resolution_hours,
                avg_response_hours,
            ]
        )


def _parse_export_tickets_csv_date_range(request):
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")
    if start_date_str and end_date_str:
        try:
            start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
            end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return HttpResponse("Invalid date format. Expected ISO 8601 format.", status=400)
        return start_date, end_date

    days_param = request.GET.get("days", "30")
    try:
        days = int(days_param)
        if days <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return HttpResponse('Invalid "days" parameter. Must be a positive integer.', status=400)
    end_date = timezone.now()
    return end_date - timedelta(days=days), end_date


def _export_tickets_csv_response(tickets, start_date, end_date):
    response = HttpResponse(content_type="text/csv")
    response[
        "Content-Disposition"
    ] = f'attachment; filename="all_tickets_{start_date.date()}_to_{end_date.date()}.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "Ticket ID",
            "Department",
            "Issue Type",
            "Status",
            "Priority",
            "Created Date",
            "Updated Date",
            "User K-Number",
            "User Name",
            "User Email",
            "Assigned To",
            "Additional Details",
            "Admin Notes",
        ]
    )
    _write_export_tickets_rows(writer, tickets)
    return response


def _write_export_tickets_rows(writer, tickets):
    for ticket in tickets:
        assigned_name = (
            f"{ticket.assigned_to.first_name} {ticket.assigned_to.last_name}"
            if ticket.assigned_to
            else ""
        )
        user_name = f"{ticket.user.first_name} {ticket.user.last_name}" if ticket.user else ""
        writer.writerow(
            [
                ticket.id,
                ticket.department,
                ticket.type_of_issue,
                ticket.status,
                ticket.priority,
                ticket.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                ticket.updated_at.strftime("%Y-%m-%d %H:%M:%S") if ticket.updated_at else "",
                ticket.user.k_number if ticket.user else ticket.k_number,
                user_name,
                ticket.user.email if ticket.user else ticket.email,
                assigned_name,
                ticket.additional_details,
                ticket.admin_notes or "",
            ]
        )
