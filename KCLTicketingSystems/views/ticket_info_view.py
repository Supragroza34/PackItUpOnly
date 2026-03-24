from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta

from ..models import Ticket, User, Reply
from ..serializers import ReplySerializer, TicketUpdateSerializer, StaffReassignTicket

class UserSerializer(serializers.ModelSerializer):
        """Provide user serializer endpoint behavior so authorization and response shaping stay consistent."""
        class Meta:
            """Provide meta endpoint behavior so authorization and response shaping stay consistent."""
            model = User
            fields = ['first_name', 'last_name', 'email']

class TicketSerializer(serializers.ModelSerializer):
    """Provide ticket serializer endpoint behavior so authorization and response shaping stay consistent."""
    is_overdue = serializers.SerializerMethodField()
    closed_by_role = serializers.SerializerMethodField()
    user = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    assigned_to_details = UserSerializer(source='assigned_to', read_only=True)
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        """Provide meta endpoint behavior so authorization and response shaping stay consistent."""
        model = Ticket
        fields = '__all__'

    def get_closed_by_role(self, obj):
        """Handle get closed by role requests as the HTTP boundary for the ticketing workflow. This keeps the HTTP boundary centralized for the ticketing workflow."""
        if obj.status == 'closed' and obj.closed_by_id and hasattr(obj, 'closed_by') and obj.closed_by:
            return (obj.closed_by.role or 'student').lower()
        return None

    def get_is_overdue(self, obj):
        """Handle get is overdue requests as the HTTP boundary for the ticketing workflow. This keeps the HTTP boundary centralized for the ticketing workflow."""
        cutoff = timezone.now() - timedelta(days=3)
        return obj.status in (Ticket.Status.PENDING, Ticket.Status.IN_PROGRESS) and obj.created_at < cutoff

    def get_replies(self, obj):
        """Handle get replies requests as the HTTP boundary for the ticketing workflow. This keeps the HTTP boundary centralized for the ticketing workflow."""
        replies = Reply.objects.filter(ticket=obj, parent=None)
        return ReplySerializer(replies, many=True).data
    
class TicketDetailView(RetrieveAPIView):
    """Provide ticket detail view endpoint behavior so authorization and response shaping stay consistent."""
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

@api_view(['GET'])
def ticket_info(request, ticket_id):
    """Handle ticket info requests as the HTTP boundary for the ticketing workflow. This keeps the HTTP boundary centralized for the ticketing workflow."""
    if not request.user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    if request.user.role not in ("staff", "Staff", "admin") and not getattr(request.user, "is_superuser", False):
        return Response(status=status.HTTP_403_FORBIDDEN)
    
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    serializer = TicketSerializer(ticket)

    return Response(serializer.data)


def _staff_can_access_ticket(user, ticket):
    """Staff can access tickets assigned to them; admins can access any. This keeps the HTTP boundary centralized for the ticketing workflow."""
    if getattr(user, "is_superuser", False) or (user.role or "").lower() == "admin":
        return True
    return ticket.assigned_to_id == user.id


@api_view(['PATCH'])
def staff_ticket_update(request, ticket_id):
    """Allow staff to update ticket status (e.g. close) for tickets assigned to them. This keeps the HTTP boundary centralized for the ticketing workflow."""
    if not request.user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    if request.user.role not in ("staff", "Staff", "admin") and not getattr(request.user, "is_superuser", False):
        return Response(status=status.HTTP_403_FORBIDDEN)

    ticket = get_object_or_404(Ticket, pk=ticket_id)
    if not _staff_can_access_ticket(request.user, ticket):
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

    serializer = TicketUpdateSerializer(ticket, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        ticket.refresh_from_db()
        if ticket.status == Ticket.Status.CLOSED:
            ticket.closed_by = request.user
            ticket.save(update_fields=["closed_by"])
        ticket.refresh_from_db()
        return Response(TicketSerializer(ticket).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH', 'PUT'])
def staff_ticket_reassign(request, ticket_id):
    """Staff option to reassign ticket. This keeps the HTTP boundary centralized for the ticketing workflow."""
    if not request.user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    if request.user.role not in ("staff", "Staff", "admin") and not getattr(request.user, "is_superuser", False):
        return Response(status=status.HTTP_403_FORBIDDEN)
    
    try:
        ticket = Ticket.objects.get(id=ticket_id)
        
        # Use serializer for partial update
        serializer = StaffReassignTicket(ticket, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            ticket.refresh_from_db()
            # Return full ticket data with nested user and assigned_to_details
            return Response(TicketSerializer(ticket).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Ticket.DoesNotExist:
        return Response({'error': 'Ticket not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

# ================= STAFF IN SAME DEPARTMENT FOR REASSIGNMENT =================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def department_staff_list(request):
    """Get list of staff and admin users for ticket reassignment (dropdown: staff and admin only). This keeps the HTTP boundary centralized for the ticketing workflow."""
    try:
        staff = User.objects.filter(
            role__in=[User.Role.STAFF, User.Role.ADMIN], 
            department=request.user.department
        ).annotate(
            ticket_count=Count('assigned_tickets', filter=Q(assigned_tickets__status__in=[Ticket.Status.PENDING, Ticket.Status.IN_PROGRESS]))
        ).order_by('ticket_count').values(
            'id', 'username', 'first_name', 'last_name', 'email', 'role', 'department', 'ticket_count',
        )
        return Response({'staff': list(staff)})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    