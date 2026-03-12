from django.db import models
from .ticket import Ticket
from .user import User

class Reply(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticket = models.ForeignKey(Ticket, related_name= "replies", on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    leaf_replies = models.ManyToManyField("self", symmetrical=False, blank=True)
    
    class Meta:
        ordering = ('created_at',)

    def __str__(self):
        return self.body