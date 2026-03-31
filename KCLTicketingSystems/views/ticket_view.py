"""Legacy HTML ticket form and unauthenticated ticket submission API."""
import os

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..models import Ticket, Attachment
from ..serializers import TicketSubmitSerializer


@api_view(["POST"])
def submit_ticket(request):
    """Submit a ticket using serializer validation and optional attachments."""
    files = request.FILES.getlist("attachments")
    file_error = _validate_attachments(files)
    if file_error:
        return Response({"errors": {"attachments": file_error}}, status=status.HTTP_400_BAD_REQUEST)
    serializer = TicketSubmitSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"errors": _flatten_errors(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)
    try:
        ticket = Ticket.objects.create(**serializer.validated_data)
        _attach_files(ticket, files)
        return Response(
            {"message": "Ticket submitted successfully", "ticket_id": ticket.id, "attachments_count": len(files)},
            status=status.HTTP_201_CREATED,
        )
    except Exception as exc:  # noqa: BLE001
        return Response({"errors": {"general": f"An error occurred: {str(exc)}"}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _attach_files(ticket, files):
    for file in files:
        Attachment.objects.create(ticket=ticket, file=file, original_filename=file.name)


def _validate_attachments(files):
    max_size = 10 * 1024 * 1024
    allowed_ext = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx", ".txt"}
    for file in files:
        if file.size > max_size:
            return f"{file.name} exceeds the maximum file size of 10MB"
        if os.path.splitext(file.name)[1].lower() not in allowed_ext:
            return f"{file.name} has an invalid file type. Allowed types: images, PDF, DOC, DOCX, TXT"
    return None


def _flatten_errors(errors):
    flattened = {}
    for key, values in errors.items():
        if isinstance(values, list) and values:
            flattened[key] = str(values[0])
        else:
            flattened[key] = str(values)
    return flattened
