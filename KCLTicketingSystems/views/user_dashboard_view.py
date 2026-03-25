from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.db.models import Prefetch
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from ..models import Ticket, Reply
from ..serializers import ReplySerializer
from ..utils import notify_on_ticket_update, auto_close_stale_awaiting_response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    auto_close_stale_awaiting_response()

    user = request.user
    tickets = _get_user_tickets(user)
    tickets_data = _build_tickets_data(tickets)
    return JsonResponse({"user": _build_user_data(user), "tickets": tickets_data})


def _get_user_tickets(user):
    return (
        Ticket.objects.filter(user=user)
        .select_related("user", "closed_by")
        .prefetch_related(
            Prefetch("replies", queryset=Reply.objects.select_related("user").order_by("created_at"))
        )
        .order_by("-created_at")
    )


def _build_user_data(user):
    return {"id": user.id, "k_number": user.k_number}


def _closed_by_role_for_ticket(ticket):
    if ticket.status != "closed" or not ticket.closed_by_id:
        return None
    role = ticket.closed_by.role if hasattr(ticket.closed_by, "role") else "student"
    return (role or "student").lower()


def _ticket_to_dashboard_dict(ticket):
    replies_data = ReplySerializer(ticket.replies.all(), many=True).data
    return {
        "id": ticket.id,
        "type_of_issue": ticket.type_of_issue,
        "department": ticket.department,
        "additional_details": ticket.additional_details,
        "status": ticket.status,
        "priority": ticket.priority,
        "closed_by_role": _closed_by_role_for_ticket(ticket),
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        "replies": replies_data,
    }


def _build_tickets_data(tickets):
    return [_ticket_to_dashboard_dict(t) for t in tickets]


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def student_close_ticket(request, ticket_id):
    """Allow a student to close their own ticket."""
    try:
        ticket = Ticket.objects.get(id=ticket_id, user=request.user)
    except Ticket.DoesNotExist:
        return Response({'error': 'Ticket not found or access denied'}, status=status.HTTP_404_NOT_FOUND)
    if ticket.status == Ticket.Status.CLOSED:
        return Response({'error': 'Ticket is already closed'}, status=status.HTTP_400_BAD_REQUEST)
    ticket.status = Ticket.Status.CLOSED
    ticket.closed_by = request.user
    ticket.save()
    notify_on_ticket_update(ticket, updated_by=request.user)

    return Response({'success': True, 'status': ticket.status, 'closed_by_role': (request.user.role or 'student').lower()})


