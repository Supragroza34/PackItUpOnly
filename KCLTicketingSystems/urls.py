from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views.auth import RegisterView
from .views.users import MeView
from .views.staff_dashboard_view import staff_dashboard
from .views.reply_view import ReplyCreateView, ticket_replies
from .views.ticket_info_view import TicketDetailView
from .views.ticket_create_view import TicketCreateView
from .views.notification_view import notifications_list, mark_notification_read
from .views.staff_directory_view import staff_directory
from .views.staff_meeting_view import staff_meeting
from .views.ticket_pdf_view import ticket_pdf


urlpatterns = [
    path("auth/register/", RegisterView.as_view()),
    path("auth/token/", TokenObtainPairView.as_view()),
    path("auth/token/refresh/", TokenRefreshView.as_view()),
    path("users/me/", MeView.as_view()),
    path("staff-dashboard/", staff_dashboard, name="staff_dashboard"),
    path("replies/create/", ReplyCreateView.as_view()),
    path("tickets/<int:ticket_id>/replies/", ticket_replies, name="ticket_replies"),
    path("tickets/", TicketCreateView.as_view()),
    path('tickets/<int:pk>', TicketDetailView.as_view()),
    path("notifications/", notifications_list),
    path("notifications/<int:pk>/read/", mark_notification_read),
    path("staff/", staff_directory, name="staff-directory"),
    path("staff/<int:staff_id>/", staff_meeting, name="staff-meeting"),
    path('tickets/<int:ticket_id>/pdf/', ticket_pdf, name="ticket_pdf"),
]


