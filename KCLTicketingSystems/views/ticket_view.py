from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..models import Ticket, Attachment
import re
import os

# Create your views here.

def ticket_form(request):
    """
    Display the ticket form page
    """
    return render(request, 'ticket_form.html')

@api_view(['POST'])
def submit_ticket(request):
    """
    API endpoint to submit a ticket with validation and file attachments
    """
    # Handle both JSON and FormData
    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.POST
        files = request.FILES.getlist('attachments')
    else:
        data = request.data
        files = []
    
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
    
    # Validate file attachments
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.txt']
    
    if files:
        for file in files:
            # Check file size
            if file.size > MAX_FILE_SIZE:
                errors['attachments'] = f'{file.name} exceeds the maximum file size of 10MB'
                break
            
            # Check file extension
            file_ext = os.path.splitext(file.name)[1].lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                errors['attachments'] = f'{file.name} has an invalid file type. Allowed types: images, PDF, DOC, DOCX, TXT'
                break
    
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
        
        # Save attachments if any
        attachment_count = 0
        if files:
            for file in files:
                attachment = Attachment.objects.create(
                    ticket=ticket,
                    file=file,
                    original_filename=file.name
                )
                attachment_count += 1
        
        response_data = {
            'message': 'Ticket submitted successfully',
            'ticket_id': ticket.id,
            'attachments_count': attachment_count
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response(
            {'errors': {'general': f'An error occurred: {str(e)}'}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
