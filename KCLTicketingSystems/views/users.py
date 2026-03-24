from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from ..serializers import UserSerializer

class MeView(generics.RetrieveUpdateAPIView):
    """
    Provides an endpoint for a user to retrieve and update their own profile data.
    This keeps the HTTP boundary centralized for the ticketing workflow.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        # Explicitly overriding get_object to bypass URL primary keys.
        # This guarantees users can only ever access the profile tied to their auth token.
        """Handle get object requests as the HTTP boundary for the ticketing workflow. This keeps the HTTP boundary centralized for the ticketing workflow."""
        return self.request.user