from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    k_number = models.CharField(max_length=20, blank=True, default='')
    department = models.CharField(max_length=255, blank=True)

    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        STAFF = "staff", "Staff"
        ADMIN = "admin", "Admin"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['k_number'],
                condition=models.Q(k_number__gt=''),
                name='unique_k_number_when_not_empty'
            )
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.k_number})" if self.k_number else f"{self.first_name} {self.last_name}"