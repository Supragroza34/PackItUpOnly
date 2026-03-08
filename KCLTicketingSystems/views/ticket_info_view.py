from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from ..models import Ticket, User
from ..serializers import ReplySerializer, StaffReassignTicket

class UserSerializer(serializers.ModelSerializer):
        class Meta:
            model = User
            fields = ['first_name', 'last_name', 'email']

class TicketSerializer(serializers.ModelSerializer):
    is_overdue = serializers.SerializerMethodField()
    user = UserSerializer(read_only=True)
    replies = ReplySerializer(many=True, read_only=True)
    assigned_to_details = UserSerializer(source='assigned_to', read_only=True)
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )


    class Meta:
        model = Ticket
        fields = '__all__'

    def get_is_overdue(self, obj):
        cutoff = timezone.now() - timedelta(days=3)
        return obj.status in (Ticket.Status.PENDING, Ticket.Status.IN_PROGRESS) and obj.created_at < cutoff

class TicketDetailView(RetrieveAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

@api_view(['GET'])
def ticket_info(request, ticket_id):
    if not request.user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    if request.user.role not in ("staff", "Staff", "admin") and not getattr(request.user, "is_superuser", False):
        return Response(status=status.HTTP_403_FORBIDDEN)
    
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    serializer = TicketSerializer(ticket)

    return Response(serializer.data)


@api_view(['PATCH', 'PUT'])
def staff_ticket_reassign(request, ticket_id):
    """Staff option to reassign ticket"""
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
    """Get list of staff and admin users for ticket reassignment (dropdown: staff and admin only)."""
    try:
        staff = User.objects.filter(
            role__in=[User.Role.STAFF, User.Role.ADMIN], 
            department=request.user.department
        ).annotate(
            ticket_count=Count('assigned_tickets')
        ).order_by('ticket_count').values(
            'id', 'username', 'first_name', 'last_name', 'email', 'role', 'department', 'ticket_count',
        )
        return Response({'staff': list(staff)})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    