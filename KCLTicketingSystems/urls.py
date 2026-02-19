from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views.auth import RegisterView
from .views.users import MeView
from .views.ticket_search_view import ticket_search

urlpatterns = [
    path("auth/register/", RegisterView.as_view()),
    path("auth/token/", TokenObtainPairView.as_view()),
    path("auth/token/refresh/", TokenRefreshView.as_view()),
    path("users/me/", MeView.as_view()),
    path("tickets/", ticket_search, name="ticket_search"),
]
