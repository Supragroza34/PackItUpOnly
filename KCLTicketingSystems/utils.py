from .models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

def notify_admin_on_ticket(ticket):
    """Notify all users with role='admin' that a new ticket was created."""
    admins = User.objects.filter(role='admin')
    for admin in admins:
        Notification.objects.create(
            user=admin,
            title="New Ticket Submitted",
            message=f"{ticket.user.get_full_name()} submitted a new ticket: {ticket.type_of_issue}",
            ticket=ticket
        )

def notify_staff_on_assignment(ticket, staff_user):
    """Notify staff when a ticket is assigned to them."""
    Notification.objects.create(
        user=staff_user,
        title="Ticket Assigned",
        message=f"You have been assigned ticket #{ticket.id}: {ticket.type_of_issue}",
        ticket=ticket
    )

def notify_user_on_reply(ticket, reply_user):
    """Notify ticket owner when staff replies."""
    if ticket.user != reply_user:
        Notification.objects.create(
            user=ticket.user,
            title="New Reply on Your Ticket",
            message=f"{reply_user.get_full_name()} replied to your ticket: {ticket.type_of_issue}",
            ticket=ticket
        )