"""URL routes for the AI chatbot app."""

from django.urls import path
from . import views

urlpatterns = [
    path("chat/", views.chat),
]
