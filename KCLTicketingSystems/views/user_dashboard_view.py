from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ..models import Ticket


def user_dashboard(request):
    tickets = Ticket.objects.all().order_by('-created_at')

    context = {
        'user': request.user,
        'tickets': tickets
    }

    return render (request, 'user_dashboard.html', context)