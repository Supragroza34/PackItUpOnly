from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views.auth import RegisterView
from .views.users import MeView

urlpatterns = [
    path("auth/register/", RegisterView.as_view()),
    path("auth/token/", TokenObtainPairView.as_view()),
    path("auth/token/refresh/", TokenRefreshView.as_view()),
    path("users/me/", MeView.as_view()),
]
