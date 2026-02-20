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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def staff_dashboard(request):
    # Check if user has staff role (optional - remove if all authenticated users can access)
    user_role = getattr(request.user, 'role', None)
    if user_role and user_role not in ["Staff", "admin"]:
        return Response(
            {"error": "Staff access required"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    filter_options = request.GET.get("filtering", "open")
    cutoff = timezone.now() - timedelta(days=3)

    tickets = Ticket.objects.all()

    if filter_options == "open":
        tickets = (tickets.filter(status='Open'))
    elif filter_options == "closed":
        tickets = (tickets.filter(status='Closed'))
    elif filter_options == "overdue":
        tickets = tickets.filter(status='Open', created_at__lt=cutoff)
    elif filter_options == "all":
        pass  # leave as all
    else:
        filter_options = ""

    tickets = tickets.order_by("created_at")
    serializer = TicketSerializer(tickets, many = True)

    return Response(serializer.data)

    