from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views.auth import RegisterView
from .views.users import MeView
from .views.reply_view import ReplyCreateView, ReplyView
from .views.ticket_info_view import TicketDetailView

urlpatterns = [
    path("auth/register/", RegisterView.as_view()),
    path("auth/token/", TokenObtainPairView.as_view()),
    path("auth/token/refresh/", TokenRefreshView.as_view()),
    path("users/me/", MeView.as_view()),
    path("replies/create/", ReplyCreateView.as_view()),
    path('reply/<int:ticket_id>/', ReplyView.as_view()),
    path('tickets/<int:pk>', TicketDetailView.as_view()),
]
