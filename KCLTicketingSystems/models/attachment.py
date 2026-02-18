from django.db import models
from .ticket import Ticket
import os


def attachment_upload_path(instance, filename):
    """
    Generate upload path for attachments: attachments/ticket_{ticket_id}/{filename}
    """
    if instance.ticket and instance.ticket.id:
        return f'attachments/ticket_{instance.ticket.id}/{filename}'
    else:
        # Fallback for when ticket hasn't been saved yet
        return f'attachments/temp/{filename}'


class Attachment(models.Model):
    """
    Model to store file attachments for tickets
    """
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to=attachment_upload_path)
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Attachment'
        verbose_name_plural = 'Attachments'
    
    def __str__(self):
        return f"{self.original_filename} - Ticket #{self.ticket.id}"
    
    def save(self, *args, **kwargs):
        # Store original filename before saving
        if self.file and not self.original_filename:
            self.original_filename = os.path.basename(self.file.name)
        # Store file size
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)

