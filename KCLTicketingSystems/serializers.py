from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models.ticket import Ticket
from .models.reply import Reply

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'k_number', 'department', 'role', 'is_staff', 'is_superuser']
        read_only_fields = ['id', 'role', 'is_staff', 'is_superuser']


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 
                  'k_number', 'department']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class ReplySerializer(serializers.ModelSerializer):
    # user = UserSerializer(read_only=True)
    user_username = serializers.CharField(source="user.username", read_only=True)
    # ticket = TicketSerializer(read_only=True)

    class Meta:
        model = Reply
        fields = "__all__"
        read_only_fields = ['created_at', 'updated_at']

class ReplyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model=Reply
        fields = ['ticket', 'body']   

class TicketSerializer(serializers.ModelSerializer):
    """Serializer for Ticket model - Admin view"""
    user = UserSerializer(read_only=True)
    assigned_to_details = UserSerializer(source='assigned_to', read_only=True)
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )
    
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
