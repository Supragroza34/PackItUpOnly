from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from ..models import Ticket
from ..serializers import TicketCreateSerializer


class TicketCreateView(generics.CreateAPIView):
    """Create a ticket for the authenticated user."""
    queryset = Ticket.objects.all()
    serializer_class = TicketCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
