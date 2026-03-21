from django.db import models
from .ticket import Ticket
from .user import User

class Reply(models.Model):
    # Foreign key tracking the specific
    # user who authored this reply
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Foreign key linking the reply
    # directly to the parent ticket
    ticket = models.ForeignKey(Ticket, related_name= "replies", on_delete=models.CASCADE)
    # Text field containing the actual
    # message or content of the reply
    body = models.TextField()
    # Automatically set the field to the current
    # date and time when the reply is posted
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE
    )

    # Many-to-many field allowing threaded
    # replies or hierarchical comments
    leaf_replies = models.ManyToManyField("self", symmetrical=False, blank=True)
    
    class Meta:
        ordering = ('created_at',)
        indexes = [
            models.Index(fields=["ticket", "parent"]),
        ]

    def __str__(self):
        return f"{self.body} (posted at {self.created_at})"