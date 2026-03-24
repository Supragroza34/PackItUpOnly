from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models.user import User
from ..serializers import StaffListSerializer

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def staff_directory(request):
    """
    Retrieves a list of staff members, optionally filtered by department.
    This keeps the HTTP boundary centralized for the ticketing workflow.
    """
    qs = User.objects.filter(role=User.Role.STAFF)

    department = request.query_params.get("department")
    if department:
        qs = qs.filter(department__iexact=department)

    qs = qs.order_by("last_name", "first_name")
    return Response(StaffListSerializer(qs, many=True).data)