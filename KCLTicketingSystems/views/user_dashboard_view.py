from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from ..models import Ticket
from ..serializers import ReplySerializer
from ..utils import notify_on_ticket_update


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    user = request.user
    tickets = Ticket.objects.filter(user=user).select_related('user', 'closed_by').prefetch_related('replies').order_by('-created_at')

    # Prepare list to hold ticket data
    tickets_data = []
    for t in tickets:
        replies_data = ReplySerializer(t.replies.all(), many=True).data
        closed_by_role = None
        if t.status == "closed" and t.closed_by_id:
            closed_by_role = (t.closed_by.role or "student").lower() if hasattr(t.closed_by, "role") else "student"
        tickets_data.append({
            "id": t.id,
            "type_of_issue": t.type_of_issue,
            "department": t.department,
            "additional_details": t.additional_details,
            "status": t.status,
            "priority": t.priority,
            "closed_by_role": closed_by_role,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "replies": replies_data,
        })

    user_data = {
        "id": user.id,
        "k_number": user.k_number,
    }

    # Return the final JSON response containing user and tickets data
    return JsonResponse({
        "user": user_data,
        "tickets": tickets_data
    })


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


