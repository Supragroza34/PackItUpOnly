from django.db import models
from .ticket import Ticket

class Reply(models.Model):
    #user = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at',)

    def __str__(self):
        return f"{self.body}"