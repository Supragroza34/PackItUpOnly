"""Authenticated `/users/me/` retrieve and update using the custom User serializer."""

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from ..serializers import UserSerializer

class MeView(generics.RetrieveUpdateAPIView):
    """Expose and update the logged-in user as `UserSerializer`."""

    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
