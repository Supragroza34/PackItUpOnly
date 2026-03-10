from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Count
from .models.ticket import Ticket
from .models.reply import Reply

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    role = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'k_number', 'department', 'role', 'is_staff', 'is_superuser']
        read_only_fields = ['id', 'role', 'is_staff', 'is_superuser']
    
    def get_role(self, obj):
        """Return 'admin' for superusers, otherwise return the actual role"""
        if obj.is_superuser:
            return 'admin'
        return obj.role


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8)
    k_number = serializers.CharField(required=True, allow_blank=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 
                  'k_number', 'department']

    def validate_k_number(self, value):
        """Validate k_number uniqueness"""
        if User.objects.filter(k_number=value).exists():
            raise serializers.ValidationError("A user with this K-Number already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        try:
            user.save()
        except Exception as e:
            if 'k_number' in str(e) and 'UNIQUE' in str(e):
                raise serializers.ValidationError({'k_number': 'A user with this K-Number already exists.'})
            raise
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
    replies = ReplySerializer(many=True, read_only=True)
    assigned_to_details = UserSerializer(source='assigned_to', read_only=True)
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )
    closed_by_role = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_closed_by_role(self, obj):
        if obj.status == 'closed' and obj.closed_by_id and hasattr(obj, 'closed_by') and obj.closed_by:
            return (obj.closed_by.role or 'student').lower()
        return None


class TicketListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing tickets"""
    user_name = serializers.SerializerMethodField()
    user_k_number = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()
    closed_by_role = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = ['id', 'user_name', 'user_k_number', 'department',
                  'type_of_issue', 'status', 'priority', 'assigned_to', 'assigned_to_name',
                  'closed_by_role', 'created_at', 'updated_at']
    
    def get_user_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return "Unknown"
    
    def get_user_k_number(self, obj):
        if obj.user:
            return obj.user.k_number
        return "N/A"
    
    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}"
        return None

    def get_closed_by_role(self, obj):
        if obj.status == 'closed' and obj.closed_by_id and hasattr(obj, 'closed_by') and obj.closed_by:
            return (obj.closed_by.role or 'student').lower()
        return None


class TicketCreateSerializer(serializers.ModelSerializer):
    """Serializer for authenticated users creating a ticket (user set on view)"""
    class Meta:
        model = Ticket
        fields = ['id', 'department', 'type_of_issue', 'additional_details', 'priority']
        read_only_fields = ['id']
        extra_kwargs = {
            'priority': {'required': False},
        }
    
    def create(self, validated_data):
        department = validated_data.get("department")

        # Find staff in the same department with the least tickets
        staff = User.objects.filter(
            role__in=[User.Role.STAFF, User.Role.ADMIN],
            department=department
        ).annotate(
            ticket_count=Count("assigned_tickets")
        ).order_by("ticket_count").first()

        validated_data["assigned_to"] = staff

        return Ticket.objects.create(**validated_data)    


class TicketUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin updating tickets"""
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Ticket
        fields = ['status', 'priority', 'assigned_to', 'admin_notes']

class StaffReassignTicket(serializers.ModelSerializer):
    """Serializer for staff to reassign tickets"""
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role="staff"),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Ticket
        fields = ['assigned_to']            

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
