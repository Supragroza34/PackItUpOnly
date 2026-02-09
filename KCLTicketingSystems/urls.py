from django.urls import path
from . import views

urlpatterns = [
    # API endpoint for ticket submission
    path('api/submit-ticket/', views.submit_ticket, name='submit_ticket'),
    
    # Custom Admin dashboard URLs
    path('dashboard/login/', views.admin_login, name='admin_login'),
    path('dashboard/logout/', views.admin_logout, name='admin_logout'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/ticket/<int:ticket_id>/', views.admin_ticket_detail, name='admin_ticket_detail'),
]

