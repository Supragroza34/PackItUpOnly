"""
DRF serializers for the ticketing API.

Exposes read/write shapes for users, tickets, replies, staff lists, office hours,
and meeting requests. Used by REST views under ``KCLTicketingSystems.views``.
"""
import re

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Count
from .models.ticket import Ticket
from .models.reply import Reply
from .models.user import User
from .models.office_hours import OfficeHours
from .models.meeting_request import MeetingRequest
from .sanitizer import sanitize_additional_details

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
        """Validate k_number format and uniqueness."""
        value = value.strip()
        if not value.isdigit() or len(value) != 8:
            raise serializers.ValidationError("K-Number must be exactly 8 digits.")
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
    """Nested reply with author metadata and recursive ``children`` for threaded UI."""
    user_username = serializers.CharField(source="user.username", read_only=True)
    user_role = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = Reply
        fields = "__all__"
        read_only_fields = ['created_at', 'updated_at']

    def get_user_role(self, obj):
        """Return the role of the reply author so callers can style messages correctly."""
        if obj.user is None:
            return "student"
        if getattr(obj.user, "is_superuser", False):
            return "admin"
        return (obj.user.role or "student").lower()

    def get_children(self, obj):
        children = obj.children.all()
        return ReplySerializer(children, many=True, context=self.context).data    

class ReplyCreateSerializer(serializers.ModelSerializer):
    """Input serializer for POSTing a new reply (body, optional parent, ticket)."""
    class Meta:
        model=Reply
        fields = ['ticket', 'body', 'parent',]   

    def validate_body(self, value):
        """Reject blank or whitespace-only reply bodies."""
        if not value or not value.strip():
            raise serializers.ValidationError("Reply body cannot be empty.")
        return value.strip()

    def validate(self, attrs):
        """Block replies to closed tickets at the serializer level."""
        ticket = attrs.get('ticket')
        parent = attrs.get('parent')
        if ticket and ticket.status == Ticket.Status.CLOSED:
            raise serializers.ValidationError(
                {"ticket": "Cannot add a reply to a closed ticket."}
            )
        if ticket and parent and parent.ticket_id != ticket.id:
            raise serializers.ValidationError(
                {"parent": "Parent reply must belong to the same ticket."}
            )
        return attrs

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
        """Lowercased role of the user who closed the ticket, if status is closed."""
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
        """Lowercased role of the user who closed the ticket, if status is closed."""
        if obj.status == 'closed' and obj.closed_by_id and hasattr(obj, 'closed_by') and obj.closed_by:
            return (obj.closed_by.role or 'student').lower()
        return None


class TicketSubmitSerializer(serializers.ModelSerializer):
    """Serializer for public ticket submission with legacy contact fields."""

    class Meta:
        model = Ticket
        fields = [
            "name",
            "surname",
            "k_number",
            "k_email",
            "department",
            "type_of_issue",
            "additional_details",
        ]
        extra_kwargs = {
            "name": {"required": True, "allow_blank": False},
            "surname": {"required": True, "allow_blank": False},
            "k_number": {"required": True, "allow_blank": False},
            "k_email": {"required": True, "allow_blank": False},
            "department": {"required": True, "allow_blank": False},
            "type_of_issue": {"required": True, "allow_blank": False},
            "additional_details": {"required": True, "allow_blank": False},
        }

    def validate_name(self, value):
        value = (value or "").strip()
        if re.search(r"\d", value):
            raise serializers.ValidationError("Name cannot contain numbers")
        return value

    def validate_surname(self, value):
        value = (value or "").strip()
        if re.search(r"\d", value):
            raise serializers.ValidationError("Surname cannot contain numbers")
        return value

    def validate_k_number(self, value):
        value = (value or "").strip()
        if re.search(r"[a-zA-Z]", value):
            raise serializers.ValidationError("K-Number cannot contain letters")
        if len(value) > 8:
            raise serializers.ValidationError("K-Number cannot be more than 8 digits")
        return value

    def validate_k_email(self, value):
        return (value or "").strip()

    def validate_department(self, value):
        value = (value or "").strip()
        valid_departments = {"Informatics", "Engineering", "Medicine"}
        if value not in valid_departments:
            raise serializers.ValidationError("Invalid department selected")
        return value

    def validate_type_of_issue(self, value):
        return (value or "").strip()

    def validate_additional_details(self, value):
        return (value or "").strip()

    def validate(self, attrs):
        k_number = attrs.get("k_number", "")
        k_email = attrs.get("k_email", "")
        if not k_number:
            return attrs
        pattern = rf"^K{re.escape(k_number)}@kcl\.ac\.uk$"
        if not re.match(pattern, k_email):
            raise serializers.ValidationError(
                {"k_email": "Email must be in the format: KNumber@kcl.ac.uk"}
            )
        return attrs


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
        
        # Sanitize additional_details to only allow safe HTML formatting
        additional_details = validated_data.get("additional_details", "")
        if additional_details:
            validated_data["additional_details"] = sanitize_additional_details(additional_details)

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
        queryset=User.objects.filter(role__in=["staff", "Staff", "admin", "Admin"]),
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



class StaffListSerializer(serializers.ModelSerializer):
    """Minimal staff profile fields for assignment dropdowns and directory lists."""
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", "department", "k_number"]


class OfficeHoursSerializer(serializers.ModelSerializer):
    """Serializer for OfficeHours model"""
    class Meta:
        model = OfficeHours
        fields = ['id', 'staff', 'day_of_week', 'start_time', 'end_time', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class MeetingRequestSerializer(serializers.ModelSerializer):
    """Serializer for MeetingRequest model with student and staff details"""
    student_name = serializers.SerializerMethodField()
    student_email = serializers.SerializerMethodField()
    student_k_number = serializers.SerializerMethodField()
    staff_name = serializers.SerializerMethodField()
    
    class Meta:
        model = MeetingRequest
        fields = [
            'id', 'student', 'staff', 'meeting_datetime', 'description', 
            'status', 'created_at', 'updated_at',
            'student_name', 'student_email', 'student_k_number', 'staff_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"
    
    def get_student_email(self, obj):
        return obj.student.email
    
    def get_student_k_number(self, obj):
        return obj.student.k_number
    
    def get_staff_name(self, obj):
        return f"{obj.staff.first_name} {obj.staff.last_name}"


class MeetingRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating meeting requests"""
    class Meta:
        model = MeetingRequest
        fields = ['staff', 'meeting_datetime', 'description']

    def validate(self, data):
        """Validate meeting time: must be a 15-min slot, within office hours, and not already taken."""
        from datetime import timedelta, datetime as dt_type

        meeting_datetime = data.get('meeting_datetime')
        staff = data.get('staff')

        if meeting_datetime and staff:
            # Enforce 15-minute boundary
            if meeting_datetime.minute % 15 != 0 or meeting_datetime.second != 0:
                raise serializers.ValidationError({
                    'meeting_datetime': 'Meetings must start at a 15-minute interval (e.g. 09:00, 09:15, 09:30, 09:45).'
                })

            day_name = meeting_datetime.strftime("%A")
            meeting_time = meeting_datetime.time()
            slot_end_time = (
                dt_type.combine(meeting_datetime.date(), meeting_time) + timedelta(minutes=15)
            ).time()

            # Check the full 15-minute slot fits within office hours
            office_hours = OfficeHours.objects.filter(
                staff=staff,
                day_of_week=day_name,
                start_time__lte=meeting_time,
                end_time__gte=slot_end_time,
            )

            if not office_hours.exists():
                raise serializers.ValidationError({
                    'meeting_datetime': (
                        "The selected time is not within the staff member's office hours. "
                        "Please choose an available slot."
                    )
                })

            # Check for slot conflicts (PENDING or ACCEPTED already occupies this slot)
            conflict = MeetingRequest.objects.filter(
                staff=staff,
                meeting_datetime=meeting_datetime,
                status__in=[MeetingRequest.Status.PENDING, MeetingRequest.Status.ACCEPTED]
            )
            if conflict.exists():
                raise serializers.ValidationError({
                    'meeting_datetime': 'This time slot is already taken. Please choose another.'
                })

        return data


class StaffWithOfficeHoursSerializer(serializers.ModelSerializer):
    """Extended serializer for staff that includes their office hours"""
    office_hours = OfficeHoursSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", "department", "k_number", "office_hours"]
