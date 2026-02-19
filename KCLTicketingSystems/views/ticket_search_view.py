from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from ..models.ticket import Ticket
from ..serializers import TicketSearchSerializer

ORDERING_MAP = {
    'newest': '-created_at',
    'oldest': 'created_at',
    '-created_at': '-created_at',
    'created_at': 'created_at'
}


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ticket_search(request):
    try:
        user = request.user
        user_k_number = getattr(user, 'k_number', None)
        user_email = getattr(user, 'email', None)

        if not user_k_number and not user_email:
            return Response([], status=status.HTTP_200_OK)

        tickets = Ticket.objects.all()
        tickets = tickets.filter(Q(k_number=user_k_number) | Q(k_email=user_email))

        query = request.GET.get('q', '').strip()
        if query:
            tickets = tickets.filter(
                Q(name__icontains=query)
                | Q(surname__icontains=query)
                | Q(k_number__icontains=query)
                | Q(k_email__icontains=query)
                | Q(department__icontains=query)
                | Q(type_of_issue__icontains=query)
                | Q(additional_details__icontains=query)
            )

        status_filter = request.GET.get('status')
        if status_filter and status_filter != 'all':
            tickets = tickets.filter(status=status_filter)

        ordering = ORDERING_MAP.get(request.GET.get('ordering', 'newest'), '-created_at')
        tickets = tickets.order_by(ordering)

        serializer = TicketSearchSerializer(tickets, many=True)
        return Response(serializer.data)
    except Exception as exc:
        return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
