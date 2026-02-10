from django.db import models
from ..models import User

# Create your models here.


class Ticket(models.Model):
    k_number = models.ForeignKey('User', on_delete=models.CASCADE, related_name='tickets')
    type_of_issue = models.CharField(max_length=255)
    additional_details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=255, default='Open')

    def __str__(self):
        return f"{self.name} {self.surname}  - {self.k_number}"