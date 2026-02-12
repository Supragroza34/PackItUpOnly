from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from ..models import Ticket

"""
#@login_required
def user_dashboard(request):
    User = get_user_model()
    test_user = User.objects.first()
    tickets = Ticket.objects.filter(user=test_user).order_by('-created_at')

    context = {
        'tickets': tickets,
        'user': test_user 
    }

    return render (request, 'user_dashboard.html', context)
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