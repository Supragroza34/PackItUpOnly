from django.conf import settings
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=30, blank=True)
    full_name = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.full_name or str(self.user)
