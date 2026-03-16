from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from ..models import Ticket
from ..serializers import TicketCreateSerializer

from ..utils import notify_admin_on_ticket


class TicketCreateView(generics.CreateAPIView):
    """Create a ticket for the authenticated user."""
    queryset = Ticket.objects.all()
    serializer_class = TicketCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        ticket = serializer.save(user=self.request.user)
        notify_admin_on_ticket(ticket)
