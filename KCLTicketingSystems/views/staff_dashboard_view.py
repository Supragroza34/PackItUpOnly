from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from ..models import Ticket

def staff_dashboard(request):
    filter_options = request.GET.get("filtering", "open")
    cutoff = timezone.now() - timedelta(days=3)

    tickets = Ticket.objects.all()

    if filter_options == "open":
        tickets = tickets.filter(status="Open")
    elif filter_options == "closed":
        tickets = tickets.filter(status="Closed")
    elif filter_options == "overdue":
        tickets = tickets.filter(status="Open", created_at__lt=cutoff)
    elif filter_options == "all":
        pass  # leave as all
    else:
        filter_options = "open"
        tickets = tickets.filter(status="Open")

    tickets = tickets.order_by("created_at")

    for t in tickets:
        t.is_overdue = (t.status == "Open" and t.created_at < cutoff)

    return render(request, "staff_dashboard.html", {
        "tickets": tickets,
        "filter_options": filter_options,
    })
    