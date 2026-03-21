# Import the base AbstractUser class to
# extend Django's built-in authentication
from django.contrib.auth.models import AbstractUser
# Import the standard models module
# from Django's database package
from django.db import models

class User(AbstractUser):
    # Override the default email field to
    # enforce global uniqueness across users
    email = models.EmailField(unique=True)
    # CharField to store the student's K-Number,
    # allowing blank values and defaulting to empty
    k_number = models.CharField(max_length=20, blank=True, default='')
    # CharField to specify the department a
    # staff member or student is affiliated with
    department = models.CharField(max_length=255, blank=True)

    class Role(models.TextChoices):
        # Standard role for users submitting
        # tickets and requesting meetings
        STUDENT = "student", "Student"
        # Staff role for users who process
        # tickets and manage office hours
        STAFF = "staff", "Staff"
        # Administrator role with full access
        # to all system settings and records
        ADMIN = "admin", "Admin"

    # Field to define the user's specific access
    # level, automatically defaulting to student
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )

    class Meta:
        # Explicitly define the exact database
        # table name to use for this custom model
        db_table = 'KCLTicketingSystems_user'

    def __str__(self):
        # Return the user's full name alongside their
        # K-Number if available, otherwise just the name
        return f"{self.first_name} {self.last_name} ({self.k_number})" if self.k_number else f"{self.first_name} {self.last_name}"