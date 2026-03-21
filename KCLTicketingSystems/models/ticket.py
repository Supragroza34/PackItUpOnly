from django.db import models
from django.conf import settings


class Ticket(models.Model):
    """
    Support ticket submitted by a student.

    Originally tickets stored student contact fields directly (name, surname,
    k-number, email). The current system also links tickets to the custom User
    model via the `user` foreign key. For backwards compatibility with the
    existing views and tests, we keep the denormalised contact fields on the
    Ticket model as well.
    """

    # Link to the authenticated user who submitted the ticket (when available)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tickets",
        null=True,
        blank=True,
    )

    # Denormalised student contact fields (used by legacy views/tests)
    name = models.CharField(max_length=255, blank=True, default="")
    surname = models.CharField(max_length=255, blank=True, default="")
    k_number = models.CharField(max_length=20, blank=True, default="")
    k_email = models.EmailField(blank=True, default="")

    department = models.CharField(max_length=255)
    type_of_issue = models.CharField(max_length=255)
    additional_details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In Progress"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"
        NEW = "new", "New" 
        SEEN = "seen", "Seen"
        AWAITING_RESPONSE = "awaiting_response", "Awaiting Student Response"
        REPORTED = "reported", "Reported"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
    )
    admin_notes = models.TextField(blank=True, default="")
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="closed_tickets",
    )

    def __str__(self):
        return f"{self.user} - {self.type_of_issue}"