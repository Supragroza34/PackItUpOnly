from django.shortcuts import render
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
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
    return Ticket.objects.filter(created_at__gte=week_ago).order_by('-created_at')[:10]


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def dashboard_stats(request):
    """Get dashboard statistics"""
    try:
        data = {**_get_ticket_stats(), **_get_user_stats()}
        data['recent_tickets'] = _get_recent_tickets()
        serializer = DashboardStatsSerializer(data)
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ================= TICKET MANAGEMENT =================

def _apply_ticket_search(tickets, search):
    """Apply search filter to tickets."""
    if not search:
        return tickets
    return tickets.filter(
        Q(name__icontains=search) |
        Q(surname__icontains=search) |
        Q(k_number__icontains=search) |
        Q(k_email__icontains=search) |
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
        tickets = Ticket.objects.all().order_by('-created_at')
        search = request.GET.get('search', '')
        tickets = _apply_ticket_search(tickets, search)
        tickets = _apply_ticket_filters(tickets, request)
        return Response(_paginate_tickets(tickets, request))
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
            # Return full ticket data using TicketSerializer
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
            users = users.filter(role=role_filter)
        return Response(_paginate_users(users, request))
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
    """Get list of staff users for ticket assignment"""
    try:
        staff = User.objects.filter(role__in=[User.Role.STAFF, User.Role.ADMIN]).values(
            'id', 'username', 'first_name', 'last_name', 'email', 'role'
        )
        return Response({'staff': list(staff)})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
