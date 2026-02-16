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
from django.urls import path, include
from KCLTicketingSystems import views
from KCLTicketingSystems.views import admin_views

urlpatterns = [
    path('', views.home, name='home'),
    path('reply/<int:ticket_id>/', views.reply, name="reply"),  # if ticket objects do not exist in db will return 404 error for now
    path('admin/', admin.site.urls),
    path('ticket-form/', views.ticket_form, name='ticket_form'),
    path('api/submit-ticket/', views.submit_ticket, name='submit_ticket'),
    
    # Admin Authentication
    path('api/admin/login/', admin_views.admin_login, name='admin_login'),
    path('api/admin/logout/', admin_views.admin_logout, name='admin_logout'),
    path('api/admin/current-user/', admin_views.admin_current_user, name='admin_current_user'),
    
    # Admin Dashboard
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
]
