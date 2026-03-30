"""List staff users for the directory, optionally filtered by department."""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models.user import User
from ..serializers import StaffListSerializer

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def staff_directory(request):
    """Return staff profiles for the public directory; filter by ?department=."""
    qs = User.objects.filter(role=User.Role.STAFF)

    department = request.query_params.get("department")
    if department:
        qs = qs.filter(department__iexact=department)

    qs = qs.order_by("last_name", "first_name")
    return Response(StaffListSerializer(qs, many=True).data)