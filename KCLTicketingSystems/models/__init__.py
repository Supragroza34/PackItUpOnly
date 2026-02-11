# from .user import User  # Commented out - using default Django User model
from .ticket import Ticket
from .attachment import Attachment
from .reply import Reply


__all__ = ['Ticket', 'Attachment']  # Expose models for admin and imports
