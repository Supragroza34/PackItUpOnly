from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404

from ..models import Ticket
from ..serializers import ReplyCreateSerializer, ReplySerializer


def _staff_can_access_ticket(user, ticket):
    """Staff can access tickets assigned to them; admins can access any."""
    if getattr(user, "is_superuser", False) or (user.role or "").lower() == "admin":
        return True
    return ticket.assigned_to_id == user.id


@api_view(["GET", "POST"])
def reply_details(request, ticket_id):
    """
    GET: List replies for a ticket (staff dashboard).
    POST: Create a reply for the ticket (staff only, must have access to ticket).
    """
    if not request.user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    if request.user.role not in ("staff", "Staff", "admin") and not getattr(request.user, "is_superuser", False):
        return Response(status=status.HTTP_403_FORBIDDEN)

    ticket = get_object_or_404(Ticket, pk=ticket_id)
    if not _staff_can_access_ticket(request.user, ticket):
        return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        replies = ticket.replies.all().order_by("created_at")
        serializer = ReplySerializer(replies, many=True)
        return Response(serializer.data)

    # POST: create reply
    data = {**request.data, "ticket": ticket.id}
    serializer = ReplyCreateSerializer(data=data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReplyCreateView(generics.CreateAPIView):
    serializer_class = ReplyCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(user=self.request.user)
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)