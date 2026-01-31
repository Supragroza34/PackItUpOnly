from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Ticket
import re

# Create your views here.

@api_view(['POST'])
def submit_ticket(request):
    """
    API endpoint to submit a ticket with validation
    """
    data = request.data
    
    # Extract form data
    name = data.get('name', '').strip()
    surname = data.get('surname', '').strip()
    k_number = data.get('k_number', '').strip()
    k_email = data.get('k_email', '').strip()
    department = data.get('department', '').strip()
    type_of_issue = data.get('type_of_issue', '').strip()
    additional_details = data.get('additional_details', '').strip()
    
    # Validation errors
    errors = {}
    
    # Validate name (no numbers)
    if not name:
        errors['name'] = 'Name is required'
    elif re.search(r'\d', name):
        errors['name'] = 'Name cannot contain numbers'
    
    # Validate surname (no numbers)
    if not surname:
        errors['surname'] = 'Surname is required'
    elif re.search(r'\d', surname):
        errors['surname'] = 'Surname cannot contain numbers'
    
    # Validate K-Number (no letters, only numbers, max 8 digits)
    if not k_number:
        errors['k_number'] = 'K-Number is required'
    elif re.search(r'[a-zA-Z]', k_number):
        errors['k_number'] = 'K-Number cannot contain letters'
    elif len(k_number) > 8:
        errors['k_number'] = 'K-Number cannot be more than 8 digits'
    
    # Validate email format (must be KNumber@kcl.ac.uk)
    if not k_email:
        errors['k_email'] = 'Email is required'
    else:
        # Check if email matches the pattern KNumber@kcl.ac.uk (with K prefix)
        email_pattern = rf'^K{re.escape(k_number)}@kcl\.ac\.uk$'
        if not re.match(email_pattern, k_email):
            errors['k_email'] = 'Email must be in the format: KNumber@kcl.ac.uk'
    
    # Validate department
    valid_departments = ['Informatics', 'Engineering', 'Medicine']
    if not department:
        errors['department'] = 'Department is required'
    elif department not in valid_departments:
        errors['department'] = 'Invalid department selected'
    
    # Validate type of issue
    if not type_of_issue:
        errors['type_of_issue'] = 'Type of issue is required'
    
    # Validate additional details
    if not additional_details:
        errors['additional_details'] = 'Additional details are required'
    
    # If there are validation errors, return them
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if K-Number already exists
    if Ticket.objects.filter(k_number=k_number).exists():
        return Response(
            {'errors': {'k_number': 'A ticket with this K-Number already exists'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create the ticket
    try:
        ticket = Ticket.objects.create(
            name=name,
            surname=surname,
            k_number=k_number,
            k_email=k_email,
            department=department,
            type_of_issue=type_of_issue,
            additional_details=additional_details
        )
        return Response({
            'message': 'Ticket submitted successfully',
            'ticket_id': ticket.id
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response(
            {'errors': {'general': f'An error occurred: {str(e)}'}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Admin Dashboard Views

def admin_login(request):
    """
    Admin login page
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid credentials or you do not have admin access')
    
    return render(request, 'admin/login.html')


@login_required(login_url='admin_login')
def admin_logout(request):
    """
    Admin logout
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('admin_login')


@login_required(login_url='admin_login')
def admin_dashboard(request):
    """
    Admin dashboard - lists all tickets with filtering options
    """
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    department_filter = request.GET.get('department', '')
    search_query = request.GET.get('search', '')
    
    # Start with all tickets
    tickets = Ticket.objects.all().order_by('-created_at')
    
    # Apply filters
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    
    if department_filter:
        tickets = tickets.filter(department=department_filter)
    
    if search_query:
        tickets = tickets.filter(
            k_number__icontains=search_query
        ) | tickets.filter(
            name__icontains=search_query
        ) | tickets.filter(
            surname__icontains=search_query
        )
    
    # Get statistics
    total_tickets = Ticket.objects.count()
    open_tickets = Ticket.objects.filter(status='open').count()
    in_progress_tickets = Ticket.objects.filter(status='in_progress').count()
    resolved_tickets = Ticket.objects.filter(status='resolved').count()
    closed_tickets = Ticket.objects.filter(status='closed').count()
    
    context = {
        'tickets': tickets,
        'total_tickets': total_tickets,
        'open_tickets': open_tickets,
        'in_progress_tickets': in_progress_tickets,
        'resolved_tickets': resolved_tickets,
        'closed_tickets': closed_tickets,
        'status_filter': status_filter,
        'department_filter': department_filter,
        'search_query': search_query,
        'status_choices': Ticket.STATUS_CHOICES,
    }
    
    return render(request, 'admin/dashboard.html', context)


@login_required(login_url='admin_login')
def admin_ticket_detail(request, ticket_id):
    """
    View and edit individual ticket
    """
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_status':
            new_status = request.POST.get('status')
            if new_status in dict(Ticket.STATUS_CHOICES):
                ticket.status = new_status
                ticket.save()
                messages.success(request, f'Ticket status updated to {ticket.get_status_display()}')
                return redirect('admin_ticket_detail', ticket_id=ticket.id)
        
        elif action == 'delete':
            ticket.delete()
            messages.success(request, 'Ticket deleted successfully')
            return redirect('admin_dashboard')
    
    context = {
        'ticket': ticket,
        'status_choices': Ticket.STATUS_CHOICES,
    }
    
    return render(request, 'admin/ticket_detail.html', context)
