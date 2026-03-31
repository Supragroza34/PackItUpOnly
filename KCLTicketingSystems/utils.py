"""
Cross-cutting helpers: ticket status transitions, in-app notifications.

Used by views and signals when tickets, replies, or meeting requests change.
"""
from .models import MeetingRequest, Notification, Ticket
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


def _is_staff_or_admin(user):
    """Return True if ``user`` is staff, admin, or superuser (for reply routing)."""
    if not user:
        return False
    return getattr(user, "is_superuser", False) or (getattr(user, "role", "") or "").lower() in ("staff", "admin")


def update_ticket_status_after_reply(ticket, reply_user):
    """Move ticket state based on who replied.

    Staff/admin reply -> awaiting student response.
    Student reply -> in progress.
    """
    if not ticket or ticket.status == Ticket.Status.CLOSED:
        return False

    target_status = Ticket.Status.AWAITING_RESPONSE if _is_staff_or_admin(reply_user) else Ticket.Status.IN_PROGRESS
    if ticket.status == target_status:
        return False

    ticket.status = target_status
    ticket.save(update_fields=["status"])
    return True


def auto_close_stale_awaiting_response(days=3):
    """Close tickets waiting on student response for too long.

    A ticket is auto-closed when it is currently awaiting_response and its
    latest reply is from staff/admin and older than the configured cutoff.
    """
    cutoff = timezone.now() - timedelta(days=days)
    stale_ticket_ids = []

    # Prefetch replies and users in bulk to avoid N+1
    awaiting_tickets = Ticket.objects.filter(status=Ticket.Status.AWAITING_RESPONSE).prefetch_related("replies__user")
    for ticket in awaiting_tickets:
        replies = list(ticket.replies.all())
        if not replies:
            continue
        # Find latest reply by created_at without extra queries
        latest_reply = max(replies, key=lambda r: r.created_at)
        if _is_staff_or_admin(latest_reply.user) and latest_reply.created_at <= cutoff:
            stale_ticket_ids.append(ticket.id)

    if not stale_ticket_ids:
        return 0

    return Ticket.objects.filter(
        id__in=stale_ticket_ids,
        status=Ticket.Status.AWAITING_RESPONSE,
    ).update(status=Ticket.Status.CLOSED, closed_by=None, updated_at=timezone.now())

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
        student_message = _student_ticket_update_message(ticket, updated_by)
        if student_message:
            _create_ticket_update_notification(
                user=ticket.user,
                ticket=ticket,
                message=student_message,
            )

    staff_message = _staff_ticket_update_message(ticket, updated_by)
    if staff_message:
        _create_ticket_update_notification(
            user=ticket.assigned_to,
            ticket=ticket,
            message=staff_message,
        )

    if ticket.status == Ticket.Status.CLOSED:
        _notify_admins_ticket_closed(ticket, updated_by)


def _create_ticket_update_notification(user, ticket, message):
    """Create a Notification record linking the given user, ticket, and message."""
    Notification.objects.create(
        user=user,
        title="Ticket Update",
        message=message,
        ticket=ticket,
    )


def _student_ticket_update_message(ticket, updated_by):
    """Return the appropriate notification message for the student, or None if no message applies."""
    if ticket.status == Ticket.Status.CLOSED:
        return (
            f"Your ticket '{ticket.type_of_issue}' has been closed by "
            f"{updated_by.get_full_name()}."
        )
    if ticket.assigned_to and ticket.assigned_to != updated_by:
        return (
            f"Your ticket '{ticket.type_of_issue}' has been assigned to "
            f"{ticket.assigned_to.get_full_name()}."
        )
    if ticket.status == Ticket.Status.IN_PROGRESS:
        return f"Your ticket '{ticket.type_of_issue}' is now in progress."
    return None


def _staff_ticket_update_message(ticket, updated_by):
    """Return the appropriate notification message for the assigned staff member, or None if not applicable."""
    if not ticket.assigned_to or ticket.assigned_to == updated_by:
        return None
    if ticket.status == Ticket.Status.CLOSED:
        return (
            f"The ticket '{ticket.type_of_issue}' you were assigned to "
            f"has been closed by {updated_by.get_full_name()}."
        )
    return f"You have been assigned to ticket '{ticket.type_of_issue}'."


def _notify_admins_ticket_closed(ticket, updated_by):
    """Send a closure notification to every admin except the one who performed the close."""
    admins = User.objects.filter(role="admin").exclude(id=updated_by.id)
    for admin in admins:
        _create_ticket_update_notification(
            user=admin,
            ticket=ticket,
            message=f"Ticket '{ticket.type_of_issue}' has been closed by admin.",
        )



def notify_staff_on_meeting_request(meeting_request):
    """
    Notify the staff assigned to the meeting request that a student submitted a request.
    """
    staff_user = meeting_request.staff
    student = meeting_request.student

    if not staff_user:
        return

    # Some unit tests pass a lightweight mock object (not the real MeetingRequest model).
    # Since Notification.meeting_request is a ForeignKey, only assign it when it's
    # a real model instance.
    meeting_request_fk = meeting_request if isinstance(meeting_request, MeetingRequest) else None

    Notification.objects.create(
        user=staff_user,
        title="New Meeting Request",
        message=f"{student.get_full_name()} submitted a meeting request.",
        meeting_request=meeting_request_fk,
        ticket=None,
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
        return  

    Notification.objects.create(
        user=student,
        title="Meeting Request Update",
        message=message,
        ticket=None  
    )


def notify_staff_on_student_reply(ticket, student_user):
    """
    Notify the staff assigned to a ticket when the student replies.
    """
    staff_user = ticket.assigned_to
    if staff_user and staff_user != student_user:
        Notification.objects.create(
            user=staff_user,
            title="New Student Reply",
            message=f"{student_user.get_full_name()} replied to ticket #{ticket.id}: {ticket.type_of_issue}",
            ticket=ticket
        )