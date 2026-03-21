from rest_framework import generics, permissions
from ..serializers import RegisterSerializer

class RegisterView(generics.CreateAPIView):
    """
    API endpoint to register a new user in the system.
    Permissions are explicitly set to AllowAny to ensure unauthenticated 
    visitors can successfully access the registration route.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer