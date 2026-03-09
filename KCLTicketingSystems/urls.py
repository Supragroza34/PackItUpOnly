from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views.auth import RegisterView
from .views.users import MeView
from .views.staff_dashboard_view import staff_dashboard
from .views.reply_view import ReplyCreateView
from .views.ticket_info_view import TicketDetailView
from .views.ticket_create_view import TicketCreateView
from .views.ticket_pdf_view import ticket_pdf

urlpatterns = [
    path("auth/register/", RegisterView.as_view()),
    path("auth/token/", TokenObtainPairView.as_view()),
    path("auth/token/refresh/", TokenRefreshView.as_view()),
    path("users/me/", MeView.as_view()),
    path("staff-dashboard/", staff_dashboard, name="staff_dashboard"),
    path("replies/create/", ReplyCreateView.as_view()),
    path("tickets/", TicketCreateView.as_view()),
    path('tickets/<int:pk>', TicketDetailView.as_view()),
    path('tickets/<int:ticket_id>/pdf/', ticket_pdf, name="ticket_pdf"),
]


