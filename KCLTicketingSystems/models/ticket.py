from django.db import models
from django.conf import settings

# Create your models here.


class Ticket(models.Model):
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tickets",
    )
    """
    
    name = models.CharField(max_length=255)
    surname = models.CharField(max_length=255)
    k_number = models.CharField(max_length=255)
    k_email = models.EmailField()

    department = models.CharField(max_length=255)
    type_of_issue = models.CharField(max_length=255)
    additional_details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=255, default='Open')

    def __str__(self):
        return f"{self.name} {self.surname}  - {self.k_number}"
        #return f"{self.user} - {self.type_of_issue}"