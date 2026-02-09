# from .user import User  # Commented out - using default Django User model
from .ticket import Ticket

__all__ = ['Ticket']  # Removed 'User' since we're using default Django User
