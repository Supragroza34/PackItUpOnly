from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from ..models import Ticket
from ..serializers import ReplySerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    user = request.user
    tickets = Ticket.objects.filter(user=user).select_related('user').prefetch_related('replies').order_by('-created_at')

    tickets_data = []
    for t in tickets:
        replies_data = ReplySerializer(t.replies.all(), many=True).data
        tickets_data.append({
            "id": t.id,
            "type_of_issue": t.type_of_issue,
            "department": t.department,
            "additional_details": t.additional_details,
            "status": t.status,
            "created_at": t.created_at,
            "replies": replies_data,
        })

    user_data = {
        "id": user.id,
        "k_number": user.k_number,
    }

    return JsonResponse({
        "user": user_data,
        "tickets": tickets_data
    })


