from django.db import models
from .ticket import Ticket

class Reply(models.Model):
    #user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, blank=True)
    body = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    leaf_replies = models.ManyToManyField("self", symmetrical=False, blank=True)
    
    class Meta:
        ordering = ('created_at',)

    def __str__(self):
        return self.body