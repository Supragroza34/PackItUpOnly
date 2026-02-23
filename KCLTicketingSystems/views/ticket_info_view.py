from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView
from rest_framework import serializers
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from ..models import Ticket, User
from ..serializers import ReplySerializer

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
        is_overdue = (obj.status == "Open" and obj.created_at < cutoff)
        return is_overdue

class TicketDetailView(RetrieveAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

@api_view(['GET'])
def ticket_info(request, ticket_id):
    if not request.user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    if not (request.user.role == "Staff" or request.user.role == "staff"):
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    serializer = TicketSerializer(ticket)

    return Response(serializer.data)