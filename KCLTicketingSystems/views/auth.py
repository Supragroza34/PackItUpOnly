"""Authentication-related API views (registration)."""
from rest_framework import generics, permissions
from ..serializers import RegisterSerializer


class RegisterView(generics.CreateAPIView):
    """Public endpoint to create a new user account via ``RegisterSerializer``."""

    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer
