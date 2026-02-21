from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from ..models import Ticket
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    #User = get_user_model()
    user = request.user
    #test_user = User.objects.first()
    tickets = Ticket.objects.filter(user=user).order_by('-created_at')

    """
    context = {
        'tickets': tickets,
        'user': test_user 
    }
    """

    tickets_data = [
        {
            "id": t.id,
            "type_of_issue": t.type_of_issue,
            "department": t.department,
            "additional_details": t.additional_details,
            "created_at": t.created_at,
        }
        for t in tickets
    ]

    user_data = {
        "id": user.id,
        "k_number": user.k_number,
    }

    return JsonResponse({
        "user": user_data,
        "tickets": tickets_data
    })


"""
def user_dashboard(request):
    # TEMPORARY: pick a test K-number
    test_k_number = "K1234567"
    
    # Get all tickets for this user
    tickets = Ticket.objects.filter(k_number=test_k_number).order_by('-created_at')

    context = {
        'tickets': tickets,
        'k_number': test_k_number
    }

    return render(request, 'user_dashboard.html', context)

"""