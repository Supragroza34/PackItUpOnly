from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from ..models import Ticket, User

class UserSerializer(serializers.ModelSerializer):
        class Meta:
            model = User
            fields = ['first_name', 'last_name', 'email']

class TicketSerializer(serializers.ModelSerializer):
    is_overdue = serializers.SerializerMethodField()

    k_number = UserSerializer()

    class Meta:
        model = Ticket
        fields = '__all__'

    def get_is_overdue(self, obj):
        cutoff = timezone.now() - timedelta(days=3)
        is_overdue = (obj.status == "Open" and obj.created_at < cutoff)
        return is_overdue

@api_view(['GET'])
def ticket_info(request, pk):
    if not request.user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    ticket = get_object_or_404(Ticket, pk=pk)
    serializer = TicketSerializer(ticket)

    return Response(serializer.data)