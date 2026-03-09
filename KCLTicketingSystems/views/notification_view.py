from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes

from ..models import Notification

@api_view(["GET"])
@permission_classes({IsAuthenticated})
def notifications_list (request):
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")

    data = [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read, 
            "ticket_id": n.ticket_id if n.ticket else None, 
            "created_at": n.created_at
        }
        for n in notifications 
    ]

    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, pk):
    try:
        notification = Notification.objects.get(id=pk, user=request.user)
    except Notification.DoesNotExist:
        return Response({"error": "Notification not found."}, status=404)
   
    notification.is_read = True
    notification.save()

    return Response({"success": True})
