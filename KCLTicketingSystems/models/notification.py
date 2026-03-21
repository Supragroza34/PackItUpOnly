from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Notification(models.Model):
    # Foreign key linking the notification
    # to the recipient user
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    # Short headline or subject
    # for the notification alert
    title = models.CharField(max_length=255)
    # Full text content explaining
    # the details of the notification
    message = models.TextField()
    # Optional foreign key linking this
    # alert to a specific support ticket
    ticket = models.ForeignKey("Ticket", on_delete=models.CASCADE, null=True, blank=True)
    # Optional foreign key linking this
    # alert to a specific meeting request
    meeting_request = models.ForeignKey("MeetingRequest", on_delete=models.CASCADE, null=True, blank=True)
    # Flag to track if the user has
    # seen or dismissed the notification
    is_read = models.BooleanField(default=False)
    # Automatically set the field to the current
    # date and time when the notification is generated
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"