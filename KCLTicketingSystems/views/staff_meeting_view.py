from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from ..models.user import User
from ..serializers import StaffWithOfficeHoursSerializer

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def staff_meeting(request, staff_id: int):
    staff = get_object_or_404(User, id=staff_id, role=User.Role.STAFF)
    return Response(StaffWithOfficeHoursSerializer(staff).data)