from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404

from ..models import Ticket, Reply
from ..serializers import ReplyCreateSerializer, ReplySerializer

from ..utils import notify_user_on_reply, notify_staff_on_student_reply


def _staff_can_access_ticket(user, ticket):
    """Staff can access tickets assigned to them; admins can access any."""
    if getattr(user, "is_superuser", False) or (user.role or "").lower() == "admin":
        return True
    return ticket.assigned_to_id == user.id


def _is_staff_or_admin(user):
    return getattr(user, "is_superuser", False) or (user.role or "").lower() in ("staff", "admin")


def _can_access_ticket_conversation(user, ticket):
    if _is_staff_or_admin(user):
        return _staff_can_access_ticket(user, ticket)
    return ticket.user_id == user.id


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
        replies = Reply.objects.filter(ticket=ticket_id, parent=None).select_related("user").prefetch_related("children")
        serializer = ReplySerializer(replies, many=True)
        return Response(serializer.data)

    # POST: create reply
    if ticket.status == Ticket.Status.CLOSED:
        return Response(
            {"error": "Replies are disabled because this ticket is closed"},
            status=status.HTTP_400_BAD_REQUEST,
        )
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
            reply = serializer.save(user=self.request.user)
            ticket = reply.ticket
          
            # Notify student (ticket owner) if staff replied
            notify_user_on_reply(ticket, reply.user)

            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def ticket_replies(request, ticket_id):
    """
    Ticket conversation endpoint.

    GET: list replies in chronological order.
    POST: create reply if caller can access the ticket and ticket is not closed.
    """
    ticket = get_object_or_404(Ticket, pk=ticket_id)

    if not _can_access_ticket_conversation(request.user, ticket):
        return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        replies = Reply.objects.filter(ticket=ticket, parent=None).order_by("created_at")
        serializer = ReplySerializer(replies, many=True)
        return Response(serializer.data)

    if ticket.status == Ticket.Status.CLOSED:
        return Response(
            {"error": "Replies are disabled because this ticket is closed"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = {**request.data, "ticket": ticket.id}
    serializer = ReplyCreateSerializer(data=data)
    if serializer.is_valid():
        reply = serializer.save(user=request.user)
        ticket = reply.ticket

        # Notify staff if student replied
        notify_staff_on_student_reply(ticket, reply.user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)