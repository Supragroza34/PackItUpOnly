from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404

from ..models import Ticket, Reply
from ..serializers import ReplyCreateSerializer, ReplySerializer

from ..utils import (
    notify_user_on_reply,
    notify_staff_on_student_reply,
    update_ticket_status_after_reply,
    auto_close_stale_awaiting_response,
)


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
    if not _staff_can_reply(request.user):
        return Response(status=status.HTTP_403_FORBIDDEN)

    auto_close_stale_awaiting_response()

    ticket = get_object_or_404(Ticket, pk=ticket_id)
    if not _staff_can_access_ticket(request.user, ticket):
        return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        return _reply_details_get(ticket_id=ticket_id)
    return _reply_details_post(request=request, ticket=ticket)


class ReplyCreateView(generics.CreateAPIView):
    serializer_class = ReplyCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request):
        auto_close_stale_awaiting_response()

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            reply = serializer.save(user=self.request.user)
            ticket = reply.ticket

            update_ticket_status_after_reply(ticket, reply.user)
            if _is_staff_or_admin(reply.user):
                notify_user_on_reply(ticket, reply.user)
            else:
                notify_staff_on_student_reply(ticket, reply.user)

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
    auto_close_stale_awaiting_response()

    ticket = get_object_or_404(Ticket, pk=ticket_id)

    if not _can_access_ticket_conversation(request.user, ticket):
        return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        return _ticket_replies_get(ticket=ticket)
    return _ticket_replies_post(request=request, ticket=ticket)


def _staff_can_reply(user):
    return user.role in ("staff", "Staff", "admin") or getattr(user, "is_superuser", False)


def _reply_details_get(ticket_id):
    replies = (
        Reply.objects.filter(ticket=ticket_id, parent=None)
        .select_related("user")
        .prefetch_related("children")
    )
    serializer = ReplySerializer(replies, many=True)
    return Response(serializer.data)


def _reply_details_post(request, ticket):
    if ticket.status == Ticket.Status.CLOSED:
        return Response(
            {"error": "Replies are disabled because this ticket is closed"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    data = {**request.data, "ticket": ticket.id}
    serializer = ReplyCreateSerializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    reply = serializer.save(user=request.user)
    update_ticket_status_after_reply(reply.ticket, reply.user)
    notify_user_on_reply(reply.ticket, reply.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


def _ticket_replies_get(ticket):
    replies = Reply.objects.filter(ticket=ticket, parent=None).order_by("created_at")
    serializer = ReplySerializer(replies, many=True)
    return Response(serializer.data)


def _ticket_replies_post(request, ticket):
    if ticket.status == Ticket.Status.CLOSED:
        return Response(
            {"error": "Replies are disabled because this ticket is closed"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = {**request.data, "ticket": ticket.id}
    serializer = ReplyCreateSerializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    reply = serializer.save(user=request.user)
    update_ticket_status_after_reply(reply.ticket, reply.user)

    if _is_staff_or_admin(reply.user):
        notify_user_on_reply(reply.ticket, reply.user)
    else:
        notify_staff_on_student_reply(reply.ticket, reply.user)

    return Response(serializer.data, status=status.HTTP_201_CREATED)