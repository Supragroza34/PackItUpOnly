from django.contrib import admin
from .models import Ticket, Attachment


class AttachmentInline(admin.TabularInline):
    """Inline admin for attachments"""
    model = Attachment
    extra = 0
    readonly_fields = ('original_filename', 'file_size', 'uploaded_at')
    fields = ('file', 'original_filename', 'file_size', 'uploaded_at')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """Admin configuration for Ticket model"""
    list_display = ('id', 'name', 'surname', 'k_number', 'department', 'type_of_issue', 'created_at')
    list_filter = ('department', 'created_at')
    search_fields = ('name', 'surname', 'k_number', 'k_email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [AttachmentInline]
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


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    """Admin configuration for Attachment model"""
    list_display = ('id', 'ticket', 'original_filename', 'file_size', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('original_filename', 'ticket__k_number', 'ticket__name')
    readonly_fields = ('original_filename', 'file_size', 'uploaded_at')
