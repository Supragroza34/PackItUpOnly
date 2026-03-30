"""Django forms for reply-related HTML flows (non-DRF)."""
from django import forms
from KCLTicketingSystems.models import Reply


class ReplyForm(forms.ModelForm):
    """Model form for submitting a reply body in server-rendered templates."""

    class Meta:
        model = Reply
        fields = ['body']