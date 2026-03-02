from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views.auth import RegisterView
from .views.users import MeView
from .views.ticket_search_view import ticket_search
from .views.staff_dashboard_view import staff_dashboard
from .views.reply_view import ReplyCreateView, ReplyView
from .views.ticket_info_view import TicketDetailView
from .views.ticket_create_view import TicketCreateView

urlpatterns = [
    path("auth/register/", RegisterView.as_view()),
    path("auth/token/", TokenObtainPairView.as_view()),
    path("auth/token/refresh/", TokenRefreshView.as_view()),
    path("users/me/", MeView.as_view()),
    path("tickets/", ticket_search, name="ticket_search"),
    path("tickets/create/", TicketCreateView.as_view(), name="ticket_create"),
    path('tickets/<int:pk>/', TicketDetailView.as_view(), name="ticket_detail"),
    path("staff-dashboard/", staff_dashboard, name="staff_dashboard"),
    path("replies/create/", ReplyCreateView.as_view()),
    path('reply/<int:ticket_id>/', ReplyView.as_view()),
]


