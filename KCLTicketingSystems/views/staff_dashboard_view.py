from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from ..models import Ticket


class TicketSerializer(serializers.ModelSerializer):
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = ['id', 'type_of_issue', 'status', 'is_overdue', 'k_number', 'created_at']

    def get_is_overdue(self, obj):
        cutoff = timezone.now() - timedelta(days=3)
        return obj.status == "Open" and obj.created_at < cutoff


def _check_staff_access(user):
    """Check if user has staff or admin role."""
    user_role = getattr(user, 'role', None)
    if user_role and user_role not in ["Staff", "admin"]:
        return Response(
            {"error": "Staff access required"},
            status=status.HTTP_403_FORBIDDEN
        )
    return None


def _apply_ticket_filter(tickets, filter_options):
    """Apply filtering to tickets based on filter option."""
    cutoff = timezone.now() - timedelta(days=3)
    if filter_options == "open":
        return tickets.filter(status='Open')
    if filter_options == "closed":
        return tickets.filter(status='Closed')
    if filter_options == "overdue":
        return tickets.filter(status='Open', created_at__lt=cutoff)
    return tickets


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def staff_dashboard(request):
    access_error = _check_staff_access(request.user)
    if access_error:
        return access_error
    filter_options = request.GET.get("filtering", "open")
    tickets = Ticket.objects.all()
    tickets = _apply_ticket_filter(tickets, filter_options)
    tickets = tickets.order_by("created_at")
    serializer = TicketSerializer(tickets, many=True)
    return Response(serializer.data)

    