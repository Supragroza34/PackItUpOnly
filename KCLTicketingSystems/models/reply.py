from django.db import models

class Reply(models.Model):
    #user = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    replies = models.ManyToManyField("self", symmetrical=False, blank=True)
    class Meta:
        ordering = ('created_at',)

    def __str__(self):
        return self.body