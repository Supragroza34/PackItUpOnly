"""Threaded reply model: one ticket, optional parent for nesting."""
from django.db import models
from .ticket import Ticket
from .user import User


class Reply(models.Model):
    """A message on a ticket, optionally threaded under another reply."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticket = models.ForeignKey(Ticket, related_name= "replies", on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ('created_at',)
        indexes = [
            models.Index(fields=["ticket", "parent"]),
        ]

    def __str__(self):
        return f"{self.body} (posted at {self.created_at})"