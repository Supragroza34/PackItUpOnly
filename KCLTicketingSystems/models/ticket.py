from django.db import models

# Create your models here.


class Ticket(models.Model):
    name = models.CharField(max_length=255)
    surname = models.CharField(max_length=255)
    k_number = models.CharField(max_length=255)  # Removed unique=True to allow multiple tickets per user
    k_email = models.EmailField()
    department = models.CharField(max_length=255)
    type_of_issue = models.CharField(max_length=255)
    additional_details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} {self.surname}  - {self.k_number}"