"""In-app notifications for ticket and meeting-request events."""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Notification(models.Model):
    """Per-user notification row; optional link to a ticket or meeting request."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=255)
    message = models.TextField()
    ticket = models.ForeignKey("Ticket", on_delete=models.CASCADE, null=True, blank=True)
    meeting_request = models.ForeignKey("MeetingRequest", on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"