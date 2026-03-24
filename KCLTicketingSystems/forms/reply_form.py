from django import forms
from KCLTicketingSystems.models import Reply

class ReplyForm(forms.ModelForm):
    """Define reply form form rules to keep validation policy centralized across the ticketing system. This keeps validation policy centralized for the ticketing workflow."""
    class Meta:
        """Define meta form rules to keep validation policy centralized across the ticketing system. This keeps validation policy centralized for the ticketing workflow."""
        model = Reply
        fields = ['body']