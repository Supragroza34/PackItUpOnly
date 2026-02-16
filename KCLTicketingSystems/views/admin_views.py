from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json

from ..models.ticket import Ticket
from ..models.user import User
from ..serializers import (
    TicketSerializer, 
    TicketListSerializer, 
    TicketUpdateSerializer,
    UserSerializer,
    DashboardStatsSerializer
)
from ..permissions import admin_required, IsAdmin


# ================= AUTHENTICATION =================

@csrf_exempt
def admin_login(request):
    """Admin login endpoint"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return JsonResponse(
                    {'error': 'Username and password required'},
                    status=400
                )
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.role == 'admin':
                    login(request, user)
                    return JsonResponse({
                        'success': True,
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'email': user.email,
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'role': user.role,
                        }
                    })
                else:
                    return JsonResponse(
                        {'error': 'Admin access required'},
                        status=403
                    )
            else:
                return JsonResponse(
                    {'error': 'Invalid credentials'},
                    status=401
                )
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'POST method required'}, status=405)


@admin_required
def admin_logout(request):
    """Admin logout endpoint"""
    logout(request)
    return JsonResponse({'success': True, 'message': 'Logged out successfully'})


@admin_required
def admin_current_user(request):
    """Get current admin user info"""
    return JsonResponse({
        'id': request.user.id,
        'username': request.user.username,
        'email': request.user.email,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'role': request.user.role,
    })


# ================= DASHBOARD STATISTICS =================

@admin_required
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
        students = User.objects.filter(role=User.Role.STUDENT).count()
        staff = User.objects.filter(role=User.Role.STAFF).count()
        admins = User.objects.filter(role=User.Role.ADMIN).count()
        
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
            'recent_tickets': TicketListSerializer(recent, many=True).data,
        }
        
        serializer = DashboardStatsSerializer(data)
        return JsonResponse(serializer.data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ================= TICKET MANAGEMENT =================

@admin_required
def admin_tickets_list(request):
    """Get all tickets with filtering, searching, and pagination"""
    try:
        tickets = Ticket.objects.all().order_by('-created_at')
        
        # Search
        search = request.GET.get('search', '')
        if search:
            tickets = tickets.filter(
                Q(name__icontains=search) |
                Q(surname__icontains=search) |
                Q(k_number__icontains=search) |
                Q(k_email__icontains=search) |
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
        
        return JsonResponse({
            'tickets': serializer.data,
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@admin_required
def admin_ticket_detail(request, ticket_id):
    """Get single ticket details"""
    try:
        ticket = Ticket.objects.get(id=ticket_id)
        serializer = TicketSerializer(ticket)
        return JsonResponse(serializer.data)
    except Ticket.DoesNotExist:
        return JsonResponse({'error': 'Ticket not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@admin_required
def admin_ticket_update(request, ticket_id):
    """Update ticket (status, priority, assignment, notes)"""
    if request.method not in ['PATCH', 'PUT']:
        return JsonResponse({'error': 'PATCH or PUT method required'}, status=405)
    
    try:
        ticket = Ticket.objects.get(id=ticket_id)
        data = json.loads(request.body)
        
        # Update allowed fields
        if 'status' in data:
            ticket.status = data['status']
        if 'priority' in data:
            ticket.priority = data['priority']
        if 'assigned_to' in data:
            if data['assigned_to'] is None:
                ticket.assigned_to = None
            else:
                ticket.assigned_to_id = data['assigned_to']
        if 'admin_notes' in data:
            ticket.admin_notes = data['admin_notes']
        
        ticket.save()
        serializer = TicketSerializer(ticket)
        return JsonResponse(serializer.data)
    except Ticket.DoesNotExist:
        return JsonResponse({'error': 'Ticket not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@admin_required
def admin_ticket_delete(request, ticket_id):
    """Delete a ticket"""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'DELETE method required'}, status=405)
    
    try:
        ticket = Ticket.objects.get(id=ticket_id)
        ticket.delete()
        return JsonResponse({'success': True, 'message': 'Ticket deleted successfully'})
    except Ticket.DoesNotExist:
        return JsonResponse({'error': 'Ticket not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ================= USER MANAGEMENT =================

@admin_required
def admin_users_list(request):
    """Get all users with filtering and pagination"""
    try:
        users = User.objects.all().order_by('-date_joined')
        
        # Search
        search = request.GET.get('search', '')
        if search:
            users = users.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(k_number__icontains=search)
            )
        
        # Filter by role
        role_filter = request.GET.get('role')
        if role_filter:
            users = users.filter(role=role_filter)
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = users.count()
        users_page = users[start:end]
        
        serializer = UserSerializer(users_page, many=True)
        
        return JsonResponse({
            'users': serializer.data,
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@admin_required
def admin_user_detail(request, user_id):
    """Get single user details"""
    try:
        user = User.objects.get(id=user_id)
        serializer = UserSerializer(user)
        return JsonResponse(serializer.data)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@admin_required
def admin_user_update(request, user_id):
    """Update user details (role, department, etc.)"""
    if request.method not in ['PATCH', 'PUT']:
        return JsonResponse({'error': 'PATCH or PUT method required'}, status=405)
    
    try:
        user = User.objects.get(id=user_id)
        data = json.loads(request.body)
        
        # Update allowed fields
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
        
        user.save()
        serializer = UserSerializer(user)
        return JsonResponse(serializer.data)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@admin_required
def admin_user_delete(request, user_id):
    """Delete a user"""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'DELETE method required'}, status=405)
    
    try:
        user = User.objects.get(id=user_id)
        
        # Prevent deleting self
        if user.id == request.user.id:
            return JsonResponse({'error': 'Cannot delete your own account'}, status=400)
        
        user.delete()
        return JsonResponse({'success': True, 'message': 'User deleted successfully'})
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ================= STAFF USERS FOR ASSIGNMENT =================

@admin_required
def admin_staff_list(request):
    """Get list of staff users for ticket assignment"""
    try:
        staff = User.objects.filter(role__in=[User.Role.STAFF, User.Role.ADMIN]).values(
            'id', 'username', 'first_name', 'last_name', 'email', 'role'
        )
        return JsonResponse({'staff': list(staff)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
