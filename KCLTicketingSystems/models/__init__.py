# from .user import User  # Commented out - using default Django User model
from .user import User
from .ticket import Ticket
from .ticket import *
from .attachment import Attachment
from .reply import Reply


__all__ = ['Ticket', 'Attachment']  # Expose models for admin and imports

