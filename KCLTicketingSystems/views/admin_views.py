from django.shortcuts import render
from django.db.models import Q, Count, Avg, F
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta, datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import csv

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
    return Ticket.objects.select_related('user').filter(created_at__gte=week_ago).order_by('-created_at')[:10]


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def dashboard_stats(request):
    """Get dashboard statistics"""
    try:
        # Ticket statistics
        total_tickets = Ticket.objects.count()
        pending = Ticket.objects.filter(status=Ticket.Status.PENDING).count()
        in_progress = Ticket.objects.filter(status=Ticket.Status.IN_PROGRESS).count()
        resolved = Ticket.objects.filter(status=Ticket.Status.RESOLVED).count()
        closed = Ticket.objects.filter(status=Ticket.Status.CLOSED).count()
        
        # User statistics
        total_users = User.objects.count()
        students = User.objects.filter(role=User.Role.STUDENT, is_superuser=False).count()
        staff = User.objects.filter(role=User.Role.STAFF, is_superuser=False).count()
        # Count users with admin role OR superusers
        admins = User.objects.filter(Q(role=User.Role.ADMIN) | Q(is_superuser=True)).count()
        
        # Recent tickets (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        recent = Ticket.objects.filter(created_at__gte=week_ago).order_by('-created_at')[:10]
        
        data = {
            'total_tickets': total_tickets,
            'pending_tickets': pending,
            'in_progress_tickets': in_progress,
            'resolved_tickets': resolved,
            'closed_tickets': closed,
            'total_users': total_users,
            'total_students': students,
            'total_staff': staff,
            'total_admins': admins,
            'recent_tickets': recent,  # Pass queryset, not serialized data
        }
        
        serializer = DashboardStatsSerializer(data)
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        tickets = Ticket.objects.select_related('user').all().order_by('-created_at')
        search = request.GET.get('search', '')
        if search:
            tickets = tickets.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__k_number__icontains=search) |
                Q(user__email__icontains=search) |
                Q(department__icontains=search) |
                Q(type_of_issue__icontains=search)
            )
        
        # Filters
        status_filter = request.GET.get('status')
        if status_filter:
            tickets = tickets.filter(status=status_filter)
        
        priority_filter = request.GET.get('priority')
        if priority_filter:
            tickets = tickets.filter(priority=priority_filter)
        
        department_filter = request.GET.get('department')
        if department_filter:
            tickets = tickets.filter(department=department_filter)
        
        assigned_filter = request.GET.get('assigned_to')
        if assigned_filter:
            if assigned_filter == 'unassigned':
                tickets = tickets.filter(assigned_to__isnull=True)
            else:
                tickets = tickets.filter(assigned_to_id=assigned_filter)
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = tickets.count()
        tickets_page = tickets[start:end]
        
        serializer = TicketListSerializer(tickets_page, many=True)
        
        return Response({
            'tickets': serializer.data,
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_ticket_detail(request, ticket_id):
    """Get single ticket details"""
    try:
        ticket = Ticket.objects.get(id=ticket_id)
        serializer = TicketSerializer(ticket)
        return Response(serializer.data)
    except Ticket.DoesNotExist:
        return Response({'error': 'Ticket not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH', 'PUT'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_ticket_update(request, ticket_id):
    """Update ticket (status, priority, assignment, notes)"""
    try:
        ticket = Ticket.objects.get(id=ticket_id)
        
        # Use serializer for partial update
        serializer = TicketUpdateSerializer(ticket, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            ticket.refresh_from_db()
            # Return full ticket data with nested user and assigned_to_details
            return Response(TicketSerializer(ticket).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Ticket.DoesNotExist:
        return Response({'error': 'Ticket not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        users = User.objects.all().order_by('-date_joined')
        search = request.GET.get('search', '')
        users = _apply_user_search(users, search)
        role_filter = request.GET.get('role')
        if role_filter:
            if role_filter == 'admin':
                # Include users with role=admin OR superusers
                users = users.filter(Q(role=User.Role.ADMIN) | Q(is_superuser=True))
            elif role_filter == 'student':
                # Only students, exclude superusers
                users = users.filter(role=User.Role.STUDENT, is_superuser=False)
            elif role_filter == 'staff':
                # Only staff, exclude superusers (unless they also have staff role)
                users = users.filter(role=User.Role.STAFF, is_superuser=False)
            else:
                users = users.filter(role=role_filter)
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = users.count()
        users_page = users[start:end]
        
        serializer = UserSerializer(users_page, many=True)
        
        return Response({
            'users': serializer.data,
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ================= STATISTICS AND ANALYTICS =================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def get_ticket_statistics(request):
    """Get detailed ticket statistics by department with date filtering."""
    try:
        # Get date range from query params (default: last 30 days)
        days = int(request.GET.get('days', 30))
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        # Calculate date range
        if start_date_str and end_date_str:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        else:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
        
        # Filter tickets by date range
        tickets = Ticket.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
        
        # Get all departments
        departments = tickets.values_list('department', flat=True).distinct()
        
        department_stats = []
        for dept in departments:
            dept_tickets = tickets.filter(department=dept)
            
            # Count by status
            pending = dept_tickets.filter(status=Ticket.Status.PENDING).count()
            in_progress = dept_tickets.filter(status=Ticket.Status.IN_PROGRESS).count()
            resolved = dept_tickets.filter(status=Ticket.Status.RESOLVED).count()
            closed = dept_tickets.filter(status=Ticket.Status.CLOSED).count()
            
            # Count by priority
            low = dept_tickets.filter(priority=Ticket.Priority.LOW).count()
            medium = dept_tickets.filter(priority=Ticket.Priority.MEDIUM).count()
            high = dept_tickets.filter(priority=Ticket.Priority.HIGH).count()
            urgent = dept_tickets.filter(priority=Ticket.Priority.URGENT).count()
            
            # Calculate average resolution time (for closed tickets)
            closed_tickets = dept_tickets.filter(status=Ticket.Status.CLOSED, updated_at__isnull=False)
            avg_resolution_hours = None
            if closed_tickets.exists():
                total_seconds = sum([
                    (ticket.updated_at - ticket.created_at).total_seconds()
                    for ticket in closed_tickets
                ])
                avg_resolution_hours = round(total_seconds / 3600 / closed_tickets.count(), 2)
            
            department_stats.append({
                'department': dept,
                'total_tickets': dept_tickets.count(),
                'status_breakdown': {
                    'pending': pending,
                    'in_progress': in_progress,
                    'resolved': resolved,
                    'closed': closed,
                },
                'priority_breakdown': {
                    'low': low,
                    'medium': medium,
                    'high': high,
                    'urgent': urgent,
                },
                'avg_resolution_time_hours': avg_resolution_hours,
            })
        
        # Sort by total tickets descending
        department_stats.sort(key=lambda x: x['total_tickets'], reverse=True)
        
        return Response({
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'total_tickets': tickets.count(),
            'department_statistics': department_stats,
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def export_statistics_csv(request):
    """Export statistics summary as CSV."""
    try:
        # Get date range from query params
        days = int(request.GET.get('days', 30))
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        # Calculate date range
        if start_date_str and end_date_str:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        else:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
        
        # Filter tickets by date range
        tickets = Ticket.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
        
        # Get all departments
        departments = tickets.values_list('department', flat=True).distinct()
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="ticket_statistics_{start_date.date()}_to_{end_date.date()}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Department', 
            'Total Tickets', 
            'Pending', 
            'In Progress', 
            'Resolved', 
            'Closed',
            'Low Priority',
            'Medium Priority',
            'High Priority',
            'Urgent Priority',
            'Avg Resolution Time (hours)'
        ])
        
        for dept in departments:
            dept_tickets = tickets.filter(department=dept)
            
            # Count by status
            pending = dept_tickets.filter(status=Ticket.Status.PENDING).count()
            in_progress = dept_tickets.filter(status=Ticket.Status.IN_PROGRESS).count()
            resolved = dept_tickets.filter(status=Ticket.Status.RESOLVED).count()
            closed = dept_tickets.filter(status=Ticket.Status.CLOSED).count()
            
            # Count by priority
            low = dept_tickets.filter(priority=Ticket.Priority.LOW).count()
            medium = dept_tickets.filter(priority=Ticket.Priority.MEDIUM).count()
            high = dept_tickets.filter(priority=Ticket.Priority.HIGH).count()
            urgent = dept_tickets.filter(priority=Ticket.Priority.URGENT).count()
            
            # Calculate average resolution time
            closed_tickets = dept_tickets.filter(status=Ticket.Status.CLOSED, updated_at__isnull=False)
            avg_resolution_hours = ''
            if closed_tickets.exists():
                total_seconds = sum([
                    (ticket.updated_at - ticket.created_at).total_seconds()
                    for ticket in closed_tickets
                ])
                avg_resolution_hours = round(total_seconds / 3600 / closed_tickets.count(), 2)
            
            writer.writerow([
                dept,
                dept_tickets.count(),
                pending,
                in_progress,
                resolved,
                closed,
                low,
                medium,
                high,
                urgent,
                avg_resolution_hours,
            ])
        
        return response
    except Exception as e:
        return HttpResponse(f'Error: {str(e)}', status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def export_tickets_csv(request):
    """Export all individual tickets as CSV."""
    try:
        # Get date range from query params
        days = int(request.GET.get('days', 30))
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        # Calculate date range
        if start_date_str and end_date_str:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        else:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
        
        # Filter tickets by date range
        tickets = Ticket.objects.filter(
            created_at__gte=start_date, 
            created_at__lte=end_date
        ).select_related('user', 'assigned_to').order_by('-created_at')
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="all_tickets_{start_date.date()}_to_{end_date.date()}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Ticket ID',
            'Department',
            'Issue Type',
            'Status',
            'Priority',
            'Created Date',
            'Updated Date',
            'User K-Number',
            'User Name',
            'User Email',
            'Assigned To',
            'Additional Details',
            'Admin Notes',
        ])
        
        for ticket in tickets:
            assigned_name = ''
            if ticket.assigned_to:
                assigned_name = f"{ticket.assigned_to.first_name} {ticket.assigned_to.last_name}"
            
            user_name = f"{ticket.user.first_name} {ticket.user.last_name}" if ticket.user else ''
            
            writer.writerow([
                ticket.id,
                ticket.department,
                ticket.type_of_issue,
                ticket.status,
                ticket.priority,
                ticket.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                ticket.updated_at.strftime('%Y-%m-%d %H:%M:%S') if ticket.updated_at else '',
                ticket.user.k_number if ticket.user else ticket.k_number,
                user_name,
                ticket.user.email if ticket.user else ticket.email,
                assigned_name,
                ticket.additional_details,
                ticket.admin_notes or '',
            ])
        
        return response
    except Exception as e:
        return HttpResponse(f'Error: {str(e)}', status=500)
