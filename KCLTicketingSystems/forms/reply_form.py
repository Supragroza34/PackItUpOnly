from django import forms

class ReplyForm(forms.Form):
    body = forms.CharField(
        widget=forms.Textarea(attrs={
            "placeholder": "Reply here",
        }),
        required=True,
        max_length=500,
    )