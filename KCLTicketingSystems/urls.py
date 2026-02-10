from django.urls import path
from . import views

urlpatterns = [
    # API endpoint for ticket submission
    path('api/submit-ticket/', views.submit_ticket, name='submit_ticket'),
]

