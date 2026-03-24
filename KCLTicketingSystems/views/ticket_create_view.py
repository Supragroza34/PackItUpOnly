from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from ..models import Ticket, Attachment
from ..serializers import TicketCreateSerializer

from ..utils import notify_admin_on_ticket


class TicketCreateView(generics.CreateAPIView):
    """
    API endpoint for authenticated students to create new support tickets.
    Uses CreateAPIView to leverage built-in DRF validation and creation flows.
    This keeps the HTTP boundary centralized for the ticketing workflow.
    """
    queryset = Ticket.objects.all()
    serializer_class = TicketCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Overrides the default creation to automatically associate the ticket with the logged-in user
        and to manually process multipart file uploads, as standard DRF JSON serializers 
        do not natively handle bulk file arrays efficiently.
        This keeps the HTTP boundary centralized for the ticketing workflow.
        """
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