from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes

from ..models import Notification

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notifications_list(request):
    """
    Retrieves a chronological list of notifications for the authenticated user.
    This keeps the HTTP boundary centralized for the ticketing workflow.
    """
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")

    # Manual dictionary comprehension is used here over a DRF ModelSerializer
    # to safely extract the foreign key IDs (ticket_id, meeting_request_id) 
    # without triggering N+1 database queries for the full related objects.
    data = [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read, 
            "ticket_id": n.ticket_id if n.ticket else None, 
            "meeting_request_id": n.meeting_request_id if n.meeting_request else None,
            "created_at": n.created_at
        }
        for n in notifications 
    ]

    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, pk):
    """
    Flags a specific notification as read by the user.
    This keeps the HTTP boundary centralized for the ticketing workflow.
    """
    try:
        # Enforce user=request.user to prevent users from interacting with 
        # or guessing the primary keys of notifications belonging to others.
        notification = Notification.objects.get(id=pk, user=request.user)
    except Notification.DoesNotExist:
        return Response({"error": "Notification not found."}, status=404)
   
    notification.is_read = True
    notification.save()

    return Response({"success": True})