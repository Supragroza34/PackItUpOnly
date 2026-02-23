from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt

from KCLTicketingSystems.services.email_processing import extract_ticket_info_with_ai
from ..models import Ticket

import json
import logging

logger = logging.getLogger(__name__)


def _log_request(request):
    logger.info("=" * 50)
    logger.info("Email webhook called")
    logger.info("Request data keys: %s", list(request.data.keys()))
    logger.info("Request FILES keys: %s", list(request.FILES.keys()))


def _get_email_fields(request):
    sender_email = request.data.get("from", "")
    subject = request.data.get("subject", "")
    body = request.data.get("text", "") or request.data.get("body-plain", "")
    return sender_email, subject, body


def _build_email_content(subject, sender_email, body):
    return f"Subject: {subject}\n\nFrom: {sender_email}\n\nBody:\n{body}"


def _create_ticket(extracted_data, sender_email, subject, body):
    ticket = Ticket.objects.create(
        name=extracted_data.get("name", "Email User"),
        surname=extracted_data.get("surname", "Pending"),
        k_number=extracted_data.get("k_number", "00000000"),
        k_email=extracted_data.get("k_email", sender_email),
        department=extracted_data.get("department", "Informatics"),
        type_of_issue=extracted_data.get("type_of_issue", subject),
        additional_details=extracted_data.get("additional_details", body),
    )
    logger.info("✅ Ticket created successfully! ID: %s", ticket.id)
    return ticket


def _handle_exception(exc, extracted_data):
    import traceback

    logger.error("❌ Error creating ticket: %s", exc)
    logger.error("Exception type: %s", type(exc).__name__)
    logger.error("Traceback: %s", traceback.format_exc())
    return Response(
        {
            "error": str(exc),
            "error_type": type(exc).__name__,
            "extracted_data": extracted_data,
        },
        status=400,
    )


@csrf_exempt
@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def email_webhook(request):
    """Webhook endpoint that receives emails and creates tickets."""
    _log_request(request)
    sender_email, subject, body = _get_email_fields(request)
    email_content = _build_email_content(subject, sender_email, body)
    logger.info("Extracting ticket info with AI...")
    extracted_data = extract_ticket_info_with_ai(email_content, sender_email)
    logger.info("Extracted data: %s", json.dumps(extracted_data, indent=2))
    try:
        ticket = _create_ticket(extracted_data, sender_email, subject, body)
        return Response(
            {
                "message": "Ticket created successfully",
                "ticket_id": ticket.id,
                "extracted_data": extracted_data,
            },
            status=200,
        )
    except Exception as exc:  # noqa: BLE001
        return _handle_exception(exc, extracted_data)