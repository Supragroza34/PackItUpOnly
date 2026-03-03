from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..serializers import ReplyCreateSerializer

class ReplyCreateView(generics.CreateAPIView):
    serializer_class = ReplyCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(user=self.request.user)
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)