from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from ..models import Ticket

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