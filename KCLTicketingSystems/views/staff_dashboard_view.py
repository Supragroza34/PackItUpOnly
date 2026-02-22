from rest_framework.decorators import api_view
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
        is_overdue = (obj.status == "Open" and obj.created_at < cutoff)
        return is_overdue


@api_view(['GET'])
def staff_dashboard(request):
    if not request.user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    if not request.user.role == "Staff":
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    filter_options = request.GET.get("filtering", "open")
    cutoff = timezone.now() - timedelta(days=3)

    tickets = Ticket.objects.filter(assigned_to=request.user)

    if filter_options == "open":
        tickets = (tickets.filter(status='pending'))
    elif filter_options == "closed":
        tickets = (tickets.filter(status='Closed'))
    elif filter_options == "overdue":
        tickets = tickets.filter(status='pending', created_at__lt=cutoff)
    elif filter_options == "all":
        pass  # leave as all
    else:
        filter_options = ""

    tickets = tickets.order_by("created_at")
    serializer = TicketSerializer(tickets, many = True)

    return Response(serializer.data)

    