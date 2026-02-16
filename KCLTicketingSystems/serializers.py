from rest_framework import serializers
from .models.ticket import Ticket
from .models.user import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'k_number', 'department', 'role']
        read_only_fields = ['id']


class TicketSerializer(serializers.ModelSerializer):
    """Serializer for Ticket model - Admin view"""
    assigned_to_details = UserSerializer(source='assigned_to', read_only=True)
    
    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class TicketListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing tickets"""
    assigned_to_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Ticket
        fields = ['id', 'name', 'surname', 'k_number', 'department', 
                  'type_of_issue', 'status', 'priority', 'assigned_to_name',
                  'created_at', 'updated_at']
    
    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}"
        return None


class TicketUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin updating tickets"""
    class Meta:
        model = Ticket
        fields = ['status', 'priority', 'assigned_to', 'admin_notes']


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    total_tickets = serializers.IntegerField()
    pending_tickets = serializers.IntegerField()
    in_progress_tickets = serializers.IntegerField()
    resolved_tickets = serializers.IntegerField()
    closed_tickets = serializers.IntegerField()
    total_users = serializers.IntegerField()
    total_students = serializers.IntegerField()
    total_staff = serializers.IntegerField()
    total_admins = serializers.IntegerField()
    recent_tickets = TicketListSerializer(many=True)
