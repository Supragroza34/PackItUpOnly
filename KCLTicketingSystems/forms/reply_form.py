from django import forms
from KCLTicketingSystems.models import Reply

class ReplyForm(forms.ModelForm):
    class Meta:
        model = Reply
        fields = ['body']