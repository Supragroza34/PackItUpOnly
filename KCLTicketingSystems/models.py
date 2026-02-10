from django.db import models
from django.contrib.auth.models import User
# Create your models here.

'''

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    student_id = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

'''