from django.db import models

# Create your models here.


class Ticket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    name = models.CharField(max_length=255)
    surname = models.CharField(max_length=255)
    k_number = models.CharField(max_length=255, unique=True)
    k_email = models.EmailField()
    department = models.CharField(max_length=255)
    type_of_issue = models.CharField(max_length=255)
    additional_details = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} {self.surname}  - {self.k_number}"