from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..models import Ticket, Attachment
import os
import re

# Create your views here.

def ticket_form(request):
    """
    Display the ticket form page
    """
    return render(request, 'ticket_form.html')

def _get_data_and_files(request):
    if request.content_type and "multipart/form-data" in request.content_type:
        return request.POST, request.FILES.getlist("attachments")
    return request.data, []


def _extract_fields(data):
    return {
        "name": data.get("name", "").strip(),
        "surname": data.get("surname", "").strip(),
        "k_number": data.get("k_number", "").strip(),
        "k_email": data.get("k_email", "").strip(),
        "department": data.get("department", "").strip(),
        "type_of_issue": data.get("type_of_issue", "").strip(),
        "additional_details": data.get("additional_details", "").strip(),
    }


def _validate_core_fields(fields):
    errors = {}
    _validate_name(fields["name"], errors)
    _validate_surname(fields["surname"], errors)
    _validate_k_number(fields["k_number"], errors)
    _validate_k_email(fields["k_email"], fields["k_number"], errors)
    _validate_department(fields["department"], errors)
    _validate_issue_and_details(
        fields["type_of_issue"],
        fields["additional_details"],
        errors,
    )
    return errors


def _validate_name(name, errors):
    if not name:
        errors["name"] = "Name is required"
    elif re.search(r"\d", name):
        errors["name"] = "Name cannot contain numbers"


def _validate_surname(surname, errors):
    if not surname:
        errors["surname"] = "Surname is required"
    elif re.search(r"\d", surname):
        errors["surname"] = "Surname cannot contain numbers"


def _validate_k_number(k_number, errors):
    if not k_number:
        errors["k_number"] = "K-Number is required"
    elif re.search(r"[a-zA-Z]", k_number):
        errors["k_number"] = "K-Number cannot contain letters"
    elif len(k_number) > 8:
        errors["k_number"] = "K-Number cannot be more than 8 digits"


def _validate_k_email(k_email, k_number, errors):
    if not k_email:
        errors["k_email"] = "Email is required"
        return
    pattern = rf"^K{re.escape(k_number)}@kcl\.ac\.uk$"
    if not re.match(pattern, k_email):
        errors["k_email"] = "Email must be in the format: KNumber@kcl.ac.uk"


def _validate_department(department, errors):
    valid_departments = ["Informatics", "Engineering", "Medicine"]
    if not department:
        errors["department"] = "Department is required"
    elif department not in valid_departments:
        errors["department"] = "Invalid department selected"


def _validate_issue_and_details(type_of_issue, additional_details, errors):
    if not type_of_issue:
        errors["type_of_issue"] = "Type of issue is required"
    if not additional_details:
        errors["additional_details"] = "Additional details are required"


def _validate_attachments(files):
    errors = {}
    max_size = 10 * 1024 * 1024
    allowed_ext = [".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx", ".txt"]
    for file in files:
        file_error = _single_file_error(file, max_size, allowed_ext)
        if file_error:
            errors["attachments"] = file_error
            break
    return errors


def _single_file_error(file, max_size, allowed_ext):
    if file.size > max_size:
        return f"{file.name} exceeds the maximum file size of 10MB"
    file_ext = os.path.splitext(file.name)[1].lower()
    if file_ext not in allowed_ext:
        return (
            f"{file.name} has an invalid file type. "
            "Allowed types: images, PDF, DOC, DOCX, TXT"
        )
    return None


def _create_ticket_and_attachments(fields, files):
    ticket = Ticket.objects.create(**fields)
    count = 0
    for file in files:
        Attachment.objects.create(ticket=ticket, file=file, original_filename=file.name)
        count += 1
    return ticket, count


@api_view(["POST"])
def submit_ticket(request):
    """Submit a ticket with validation and file attachments."""
    data, files = _get_data_and_files(request)
    fields = _extract_fields(data)
    errors = _collect_errors(fields, files)
    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
    try:
        ticket, count = _create_ticket_and_attachments(fields, files)
        return _success_response(ticket, count)
    except Exception as exc:  # noqa: BLE001
        return _server_error_response(exc)


def _collect_errors(fields, files):
    errors = _validate_core_fields(fields)
    if files:
        attachment_errors = _validate_attachments(files)
        errors.update(attachment_errors)
    return errors


def _success_response(ticket, count):
    return Response(
        {
            "message": "Ticket submitted successfully",
            "ticket_id": ticket.id,
            "attachments_count": count,
        },
        status=status.HTTP_201_CREATED,
    )


def _server_error_response(exc):
    return Response(
        {"errors": {"general": f"An error occurred: {str(exc)}"}},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
