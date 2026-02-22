from ..models import Reply, Ticket
from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from ..serializers import ReplySerializer, ReplyCreateSerializer


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

class ReplyView(generics.ListCreateAPIView):
    queryset = Reply.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ReplySerializer

    def list(self, request):
        queryset = self.queryset
        ticket_id = self.kwargs["ticket_id"]
        ticket = Ticket.objects.get(pk=ticket_id)
        return Reply.objects.filter(ticket=ticket).order_by("created_at")
    
    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(user=self.request.user)
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        reply = self.queryset.get(pk=pk)
        serializer = self.serializer_class(reply)
        return Response(serializer.data)

    def update(self, request, pk=None):
        reply = self.queryset.get(pk=pk)            
        serializer = self.serializer_class(reply, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)

    def delete(self, request, pk=None):
        reply = self.queryset.get(pk=pk)
        reply.delete()
        return Response(status=204)


@api_view(['GET', 'POST'])
def reply_details(request, ticket_id):
    if not request.user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    replies=Reply.objects.filter(ticket=ticket)
    serializer = ReplySerializer(replies)

    return Response(serializer.data)