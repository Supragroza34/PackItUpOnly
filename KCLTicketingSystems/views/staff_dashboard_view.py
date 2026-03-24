from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, serializers
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

from ..models import Ticket
from ..serializers import UserSerializer


def _check_staff_access(user):
    """Return None if user can access staff dashboard, else an error Response. This keeps the HTTP boundary centralized for the ticketing workflow."""
    if not user or not user.is_authenticated:
        return Response({'detail': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    if user.role not in ('staff', 'Staff', 'admin') and not getattr(user, 'is_superuser', False):
        return Response({'detail': 'Staff access required'}, status=status.HTTP_403_FORBIDDEN)
    return None


class StaffTicketSerializer(serializers.ModelSerializer):
    """Ticket list item for staff dashboard; includes submitter (user) and overdue flag. This keeps the HTTP boundary centralized for the ticketing workflow."""
    user = UserSerializer(read_only=True)
    is_overdue = serializers.SerializerMethodField()
    closed_by_role = serializers.SerializerMethodField()

    class Meta:
        """Provide meta endpoint behavior so authorization and response shaping stay consistent."""
        model = Ticket
        fields = [
            'id', 'user', 'department', 'type_of_issue', 'additional_details',
            'status', 'priority', 'assigned_to', 'closed_by_role', 'created_at', 'updated_at', 'is_overdue'
        ]

    def get_closed_by_role(self, obj):
        """Handle get closed by role requests as the HTTP boundary for the ticketing workflow. This keeps the HTTP boundary centralized for the ticketing workflow."""
        if obj.status == 'closed' and obj.closed_by_id and hasattr(obj, 'closed_by') and obj.closed_by:
            return (obj.closed_by.role or 'student').lower()
        return None

    def get_is_overdue(self, obj):
        """Handle get is overdue requests as the HTTP boundary for the ticketing workflow. This keeps the HTTP boundary centralized for the ticketing workflow."""
        cutoff = timezone.now() - timedelta(days=3)
        return obj.status in (Ticket.Status.PENDING, Ticket.Status.IN_PROGRESS) and obj.created_at < cutoff


def _apply_ticket_filter(tickets, filter_options):
    """Filter by status: open = pending|in_progress|new|seen|awaiting_student_response, closed = resolved|closed, overdue = open + old, all = all. This keeps the HTTP boundary centralized for the ticketing workflow."""
    cutoff = timezone.now() - timedelta(days=3)
    if filter_options == 'open':
        return tickets.filter(status__in=(Ticket.Status.PENDING, Ticket.Status.IN_PROGRESS, Ticket.Status.NEW, Ticket.Status.SEEN, Ticket.Status.AWAITING_RESPONSE))
    if filter_options == 'closed':
        return tickets.filter(status__in=(Ticket.Status.RESOLVED, Ticket.Status.CLOSED))
    if filter_options == 'reported':
        return tickets.filter(status__in=(Ticket.Status.REPORTED,))
    if filter_options == 'overdue':
        return tickets.filter(
            status__in=(Ticket.Status.PENDING, Ticket.Status.IN_PROGRESS, Ticket.Status.NEW, Ticket.Status.SEEN, Ticket.Status.AWAITING_RESPONSE),
            created_at__lt=cutoff
        )
    # 'all' or anything else: no status filter
    return tickets


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def staff_dashboard(request):
    """List tickets assigned to the current staff user. Supports filtering by status. This keeps the HTTP boundary centralized for the ticketing workflow."""
    access_error = _check_staff_access(request.user)
    if access_error:
        return access_error

    filter_options = request.GET.get('filtering', 'open')
    search = (request.GET.get('search') or '').strip()
    # Only show tickets assigned to this user
    tickets = (
        Ticket.objects
        .select_related('user', 'assigned_to', 'closed_by')
        .filter(assigned_to=request.user)
        .order_by('-created_at')
    )
    if search:
        tickets = tickets.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search)
        )
    tickets = _apply_ticket_filter(tickets, filter_options)
    serializer = StaffTicketSerializer(tickets, many=True)
    return Response(serializer.data)
