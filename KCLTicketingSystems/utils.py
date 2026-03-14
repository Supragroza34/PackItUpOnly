from .models import Notification, Ticket
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


def notify_on_ticket_update(ticket, updated_by):
    """
    Notify student and staff when ticket is updated, reassigned, or closed.
    Admins are only notified if ticket is closed.
    
    """

    if ticket.user and ticket.user != updated_by:
        message = None
        if ticket.status == Ticket.Status.CLOSED:
            message = f"Your ticket '{ticket.type_of_issue}' has been closed by {updated_by.get_full_name()}."
        elif ticket.assigned_to and ticket.assigned_to != updated_by:
            message = f"Your ticket '{ticket.type_of_issue}' has been assigned to {ticket.assigned_to.get_full_name()}."
        elif ticket.status == Ticket.Status.IN_PROGRESS:
            message = f"Your ticket '{ticket.type_of_issue}' is now in progress."

        if message:
            Notification.objects.create(
                user=ticket.user,
                title="Ticket Update",
                message=message,
                ticket=ticket
            )

    if ticket.assigned_to and ticket.assigned_to != updated_by:
        message = None
        if ticket.status == Ticket.Status.CLOSED:
            message = f"The ticket '{ticket.type_of_issue}' you were assigned to has been closed by {updated_by.get_full_name()}."
        else:
            message = f"You have been assigned to ticket '{ticket.type_of_issue}'."

        if message:
            Notification.objects.create(
                user=ticket.assigned_to,
                title="Ticket Update",
                message=message,
                ticket=ticket
            )

    admins = User.objects.filter(role='admin').exclude(id=updated_by.id)
    if ticket.status == Ticket.Status.CLOSED:
        for admin in admins:
            Notification.objects.create(
                user=admin,
                title="Ticket Update",
                message=f"Ticket '{ticket.type_of_issue}' has been closed by admin.",
                ticket=ticket
            )



def notify_staff_on_meeting_request(meeting_request):
    """
    Notify the staff assigned to the meeting request that a student submitted a request.
    """
    staff_user = meeting_request.staff
    student = meeting_request.student

    if staff_user:
        Notification.objects.create(
            user=staff_user,
            title="New Meeting Request",
            message=f"{student.get_full_name()} submitted a meeting request.",
            ticket=None  
        )


def notify_student_on_meeting_response(meeting_request, staff_user):
    """
    Notify the student that their meeting request has been accepted or denied.
    """
    student = meeting_request.student
    if not student:
        return

    status_text = meeting_request.status.lower()
    if status_text == "accepted":
        message = f"Your meeting request has been accepted by {staff_user.get_full_name()}."
    elif status_text == "denied":
        message = f"Your meeting request has been denied by {staff_user.get_full_name()}."
    else:
        return  # Do not notify for other statuses

    Notification.objects.create(
        user=student,
        title="Meeting Request Update",
        message=message,
        ticket=None  # optional: or link to meeting_request.id if you add FK
    )
