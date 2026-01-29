from django.urls import path
from . import views

urlpatterns = [
    path('api/submit-ticket/', views.submit_ticket, name='submit_ticket'),
]

