# Import the standard models module
# from Django's database package
from django.db import models
# Import settings to dynamically reference
# the custom User model (AUTH_USER_MODEL)
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

    # Link to the authenticated user who submitted
    # the ticket (when available in the system)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tickets",
        null=True,
        blank=True,
    )

    # CharField to store the student's first name,
    # defaults to an empty string
    name = models.CharField(max_length=255, blank=True, default="")
    # CharField to store the student's surname,
    # defaults to an empty string
    surname = models.CharField(max_length=255, blank=True, default="")
    # CharField for the unique student K-Number,
    # max length set to 20
    k_number = models.CharField(max_length=20, blank=True, default="")
    # EmailField to capture the contact
    # email address for the student
    k_email = models.EmailField(blank=True, default="")

    # CharField representing the specific
    # department the ticket is routed to
    department = models.CharField(max_length=255)
    # CharField classifying the category
    # or type of the issue (e.g., IT, Academic)
    type_of_issue = models.CharField(max_length=255)
    # TextField allowing the user to provide
    # an in-depth description of their issue
    additional_details = models.TextField()
    # Automatically set the field to the current
    # date and time when the ticket is first created
    created_at = models.DateTimeField(auto_now_add=True)
    # Automatically update the field to the current
    # date and time every time the ticket object is saved
    updated_at = models.DateTimeField(auto_now=True)

    class Status(models.TextChoices):
        # Ticket is awaiting
        # initial review by staff
        PENDING = "pending", "Pending"
        # Staff is currently actively
        # working on resolving the ticket
        IN_PROGRESS = "in_progress", "In Progress"
        # Issue has been mitigated but
        # the ticket is not officially closed yet
        RESOLVED = "resolved", "Resolved"
        # The ticket lifecycle is complete
        # and no further action is required
        CLOSED = "closed", "Closed"
        # Newly created
        # ticket flag
        NEW = "new", "New" 
        # Ticket has been viewed
        # by a staff member
        SEEN = "seen", "Seen"
        # Staff is blocked and waiting for
        # the student to provide more information
        AWAITING_RESPONSE = "awaiting_response", "Awaiting Student Response"
        REPORTED = "reported", "Reported"

    class Priority(models.TextChoices):
        # Non-critical issue
        # with no immediate deadline
        LOW = "low", "Low"
        # Standard issue requiring
        # normal processing times
        MEDIUM = "medium", "Medium"
        # Time-sensitive issue that
        # impacts student progression
        HIGH = "high", "High"
        # Critical, blocking issue
        # requiring immediate staff intervention
        URGENT = "urgent", "Urgent"

    # Stores the current status of
    # the ticket, defaulting to 'Pending'
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    # Stores the urgency of the
    # ticket, defaulting to 'Medium'
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    # Foreign key linking the ticket to the specific staff member
    # responsible for it. Sets to NULL if the staff user is deleted.
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
    )
    # TextField for administrators or staff to leave internal,
    # private notes that are hidden from the student
    admin_notes = models.TextField(blank=True, default="")
    # Foreign key tracking the exact user
    # (staff/admin) who finalized and closed the ticket
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="closed_tickets",
    )

    def __str__(self):
        return f"{self.user} - {self.type_of_issue}"