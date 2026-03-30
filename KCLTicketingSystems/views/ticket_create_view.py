"""Authenticated API to create a ticket and optional file attachments."""

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from ..models import Ticket, Attachment
from ..serializers import TicketCreateSerializer

from ..utils import notify_admin_on_ticket


class TicketCreateView(generics.CreateAPIView):
    """Create a ticket for the authenticated user."""
    queryset = Ticket.objects.all()
    serializer_class = TicketCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        ticket = serializer.save(user=self.request.user)
        
        # Handle file attachments
        files = self.request.FILES.getlist('attachments')
        for file in files:
            Attachment.objects.create(
                ticket=ticket,
                file=file,
                original_filename=file.name,
                file_size=file.size
            )
        
        notify_admin_on_ticket(ticket)
