"""Django app config for the KCL ticketing domain package."""
from django.apps import AppConfig


class KclticketingsystemsConfig(AppConfig):
    """Registers models, signals, and the ``KCLTicketingSystems`` app label."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'KCLTicketingSystems'
