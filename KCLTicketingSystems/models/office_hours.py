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
    
    # Foreign key linking the office
    # hours block to a specific staff member
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="office_hours",
        limit_choices_to={"role": "staff"}
    )
    # Stores the specific day of the week
    # when the staff member is available
    day_of_week = models.CharField(
        max_length=10,
        choices=DayOfWeek.choices,
    )
    # The exact time when the office
    # hours block begins on that day
    start_time = models.TimeField()
    # The exact time when the office
    # hours block ends on that day
    end_time = models.TimeField()
    
    # Automatically set the field to the current
    # date and time when the hours block is created
    created_at = models.DateTimeField(auto_now_add=True)
    # Automatically update the field to the current
    # date and time every time the block is saved
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