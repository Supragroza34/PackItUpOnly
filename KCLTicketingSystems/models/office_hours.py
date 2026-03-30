"""Weekly availability blocks for staff meeting scheduling."""

from django.db import models
from django.conf import settings


class OfficeHours(models.Model):
    """
    Represents a time block when a staff member is available for meetings.
    Staff can have multiple office hour blocks throughout the week.
    """
    
    class DayOfWeek(models.TextChoices):
        MONDAY = "Monday", "Monday"
        TUESDAY = "Tuesday", "Tuesday"
        WEDNESDAY = "Wednesday", "Wednesday"
        THURSDAY = "Thursday", "Thursday"
        FRIDAY = "Friday", "Friday"
        SATURDAY = "Saturday", "Saturday"
        SUNDAY = "Sunday", "Sunday"
    
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="office_hours",
        limit_choices_to={"role": "staff"}
    )
    day_of_week = models.CharField(
        max_length=10,
        choices=DayOfWeek.choices,
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'KCLTicketingSystems_office_hours'
        verbose_name_plural = "Office Hours"
        ordering = ['day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.staff} - {self.day_of_week} {self.start_time}-{self.end_time}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time")
