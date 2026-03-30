"""Student–staff meeting requests constrained by office hours."""

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


class MeetingRequest(models.Model):
    """
    Represents a meeting request from a student to a staff member.
    The meeting datetime must fall within the staff member's office hours.
    """
    
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DENIED = "denied", "Denied"
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="meeting_requests_as_student",
    )
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="meeting_requests_as_staff",
        limit_choices_to={"role": "staff"}
    )
    meeting_datetime = models.DateTimeField()
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'KCLTicketingSystems_meeting_request'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student} -> {self.staff} on {self.meeting_datetime}"

    def _validate_office_hours_window(self):
        # Import here to avoid circular import
        from .office_hours import OfficeHours

        day_name = self.meeting_datetime.strftime("%A")
        meeting_time = self.meeting_datetime.time()
        office_hours = OfficeHours.objects.filter(
            staff=self.staff,
            day_of_week=day_name,
            start_time__lte=meeting_time,
            end_time__gte=meeting_time,
        )
        if office_hours.exists():
            return
        raise ValidationError(
            f"The selected time is not within {self.staff}'s office hours. "
            f"Please choose a time slot during their available hours."
        )

    def _validate_not_in_past(self):
        if self.meeting_datetime >= timezone.now():
            return
        raise ValidationError("Cannot schedule a meeting in the past.")

    def clean(self):
        """Validates meeting datetime is in office hours and not in the past."""
        if not self.meeting_datetime:
            return
        self._validate_not_in_past()
        self._validate_office_hours_window()
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
