from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView
from rest_framework import serializers
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta

from ..models import Ticket, User
from ..serializers import ReplySerializer, TicketUpdateSerializer

class UserSerializer(serializers.ModelSerializer):
        class Meta:
            model = User
            fields = ['first_name', 'last_name', 'email']

class TicketSerializer(serializers.ModelSerializer):
    is_overdue = serializers.SerializerMethodField()
    closed_by_role = serializers.SerializerMethodField()
    user = UserSerializer(read_only=True)
    replies = ReplySerializer(many=True, read_only=True)
    assigned_to_details = UserSerializer(source='assigned_to', read_only=True)
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Ticket
        fields = '__all__'

    def get_closed_by_role(self, obj):
        if obj.status == 'closed' and obj.closed_by_id and hasattr(obj, 'closed_by') and obj.closed_by:
            return (obj.closed_by.role or 'student').lower()
        return None

    def get_is_overdue(self, obj):
        cutoff = timezone.now() - timedelta(days=3)
        return obj.status in (Ticket.Status.PENDING, Ticket.Status.IN_PROGRESS) and obj.created_at < cutoff

class TicketDetailView(RetrieveAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

@api_view(['GET'])
def ticket_info(request, ticket_id):
    if not request.user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    if request.user.role not in ("staff", "Staff", "admin") and not getattr(request.user, "is_superuser", False):
        return Response(status=status.HTTP_403_FORBIDDEN)
    
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    serializer = TicketSerializer(ticket)

    return Response(serializer.data)


def _staff_can_access_ticket(user, ticket):
    """Staff can access tickets assigned to them; admins can access any."""
    if getattr(user, "is_superuser", False) or (user.role or "").lower() == "admin":
        return True
    return ticket.assigned_to_id == user.id


@api_view(['PATCH'])
def staff_ticket_update(request, ticket_id):
    """Allow staff to update ticket status (e.g. close) for tickets assigned to them."""
    if not request.user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    if request.user.role not in ("staff", "Staff", "admin") and not getattr(request.user, "is_superuser", False):
        return Response(status=status.HTTP_403_FORBIDDEN)

    ticket = get_object_or_404(Ticket, pk=ticket_id)
    if not _staff_can_access_ticket(request.user, ticket):
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

    serializer = TicketUpdateSerializer(ticket, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        ticket.refresh_from_db()
        if ticket.status == Ticket.Status.CLOSED:
            ticket.closed_by = request.user
            ticket.save(update_fields=["closed_by"])
        ticket.refresh_from_db()
        return Response(TicketSerializer(ticket).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)