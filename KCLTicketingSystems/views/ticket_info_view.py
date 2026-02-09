from django.shortcuts import render, get_object_or_404
from ..models import Ticket

def ticket_info(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)


    return render(request, "ticket_info.html", {"ticket": ticket})