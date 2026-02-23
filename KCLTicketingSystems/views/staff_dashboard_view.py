from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from ..models import Ticket
from ..serializers import UserSerializer


class TicketSerializer(serializers.ModelSerializer):
    is_overdue = serializers.SerializerMethodField() 
    user = UserSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = "__all__"

    def get_is_overdue(self, obj):
        cutoff = timezone.now() - timedelta(days=3)
        return obj.status == "Open" and obj.created_at < cutoff


@api_view(['GET'])
def staff_dashboard(request):
    if not request.user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    if request.user.role not in ["staff", "admin"] and not request.user.is_superuser:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    filter_options = request.GET.get("filtering", "open")
    cutoff = timezone.now() - timedelta(days=3)

    tickets = Ticket.objects.filter(assigned_to=request.user)

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

    