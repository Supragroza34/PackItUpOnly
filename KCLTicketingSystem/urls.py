"""
URL configuration for KCLTicketingSystem project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""



from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

from KCLTicketingSystems import views
from AIChatbot.views import chat_page

from KCLTicketingSystems.views import admin_views, staff_dashboard_view, ticket_info_view, reply_view, staff_meeting_requests_views, notification_view
#from KCLTicketingSystems.views.email_webhook import email_webhook

from KCLTicketingSystems.views import notifications_list, mark_notification_read


urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('chat/', chat_page, name='chat_page'),
    path('ticket-form/', views.ticket_form, name='ticket_form'),
    path('api/submit-ticket/', views.submit_ticket, name='submit_ticket'),
    
    # API Routes (includes JWT auth: /api/auth/token/, /api/auth/register/, /api/users/me/)
    path("api/", include("KCLTicketingSystems.urls")),
    path("api/ai-chatbot/", include("AIChatbot.urls")),
    
    # Admin Dashboard API
    path('api/admin/dashboard/stats/', admin_views.dashboard_stats, name='admin_dashboard_stats'),
    
    # Admin Ticket Management
    path('api/admin/tickets/', admin_views.admin_tickets_list, name='admin_tickets_list'),
    path('api/admin/tickets/<int:ticket_id>/', admin_views.admin_ticket_detail, name='admin_ticket_detail'),
    path('api/admin/tickets/<int:ticket_id>/update/', admin_views.admin_ticket_update, name='admin_ticket_update'),
    path('api/admin/tickets/<int:ticket_id>/delete/', admin_views.admin_ticket_delete, name='admin_ticket_delete'),
    
    # Admin User Management
    path('api/admin/users/', admin_views.admin_users_list, name='admin_users_list'),
    path('api/admin/users/<int:user_id>/', admin_views.admin_user_detail, name='admin_user_detail'),
    path('api/admin/users/<int:user_id>/update/', admin_views.admin_user_update, name='admin_user_update'),
    path('api/admin/users/<int:user_id>/delete/', admin_views.admin_user_delete, name='admin_user_delete'),
    
    # Staff List for Assignment
    path('api/admin/staff/', admin_views.admin_staff_list, name='admin_staff_list'),
    
    # Admin Statistics and Analytics
    path('api/admin/statistics/', admin_views.get_ticket_statistics, name='admin_statistics'),
    path('api/admin/export/statistics-csv/', admin_views.export_statistics_csv, name='export_statistics_csv'),
    path('api/admin/export/tickets-csv/', admin_views.export_tickets_csv, name='export_tickets_csv'),

    # Staff Dashboard
    path('api/staff/dashboard/', staff_dashboard_view.staff_dashboard, name='staff_dashboard'),
    path('api/staff/dashboard/<int:ticket_id>/', ticket_info_view.ticket_info, name='ticket_info'),
    path('api/staff/dashboard/<int:ticket_id>/update/', ticket_info_view.staff_ticket_update, name='staff_ticket_update'),
    path('api/staff/dashboard/reply/<int:ticket_id>/', reply_view.reply_details, name="reply"),
    path('api/staff/list/', ticket_info_view.department_staff_list, name='department_staff_list'),
    path('api/staff/dashboard/<int:ticket_id>/reassign/', ticket_info_view.staff_ticket_reassign, name='staff-ticket-reassign'),
    
    # Meeting Requests - Staff Side
    path('api/staff/dashboard/meeting-requests/', staff_meeting_requests_views.meeting_request_list, name="meeting_request_list"),
    path('api/staff/dashboard/meeting-requests/<int:request_id>/accept/', staff_meeting_requests_views.meeting_request_accept, name="meeting_request_accept"),
    path('api/staff/dashboard/meeting-requests/<int:request_id>/deny/', staff_meeting_requests_views.meeting_request_deny, name="meeting_request_deny"),
    
    # Office Hours Management - Staff Side
    path('api/staff/office-hours/', staff_meeting_requests_views.office_hours_manage, name="office_hours_manage"),
    path('api/staff/office-hours/<int:hours_id>/', staff_meeting_requests_views.office_hours_delete, name="office_hours_delete"),
    
    # Meeting Requests - Student Side
    path('api/meeting-requests/', staff_meeting_requests_views.meeting_request_create, name="meeting_request_create"),

    # Available 15-minute slots for a staff member on a given date
    path('api/staff/<int:staff_id>/available-slots/', staff_meeting_requests_views.staff_available_slots, name="staff_available_slots"),
    
    path('api/dashboard/', views.user_dashboard, name="user_dashboard"),
    path('api/dashboard/tickets/<int:ticket_id>/close/', views.student_close_ticket, name='student_close_ticket'),

    path("notifications/", notifications_list, name="notifications_list"),
    path("notifications/<int:pk>/read/", mark_notification_read, name="mark_notification_read"),

    #path('api/email-webhook/', email_webhook, name='email_webhook'),


    # SPA: serve React app for all non-API/static/media routes (login, dashboard, etc.)
    re_path(r'^(?!(static/|api/|media/))(?P<path>.*)$', views.spa_catchall, name='spa_catchall')
    #Check
]


# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve React app for all other routes (login, dashboard, etc.)