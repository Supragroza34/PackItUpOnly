from django.contrib import admin
from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """Admin configuration for Ticket model"""
    list_display = ('id', 'name', 'surname', 'k_number', 'department', 'type_of_issue', 'created_at')
    list_filter = ('department', 'created_at')
    search_fields = ('name', 'surname', 'k_number', 'k_email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'surname', 'k_number', 'k_email')
        }),
        ('Ticket Information', {
            'fields': ('department', 'type_of_issue', 'additional_details')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
