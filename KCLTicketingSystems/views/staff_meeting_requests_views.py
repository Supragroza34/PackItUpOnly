from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from ..models.meeting_request import MeetingRequest
from ..models.office_hours import OfficeHours
from ..serializers import (
    MeetingRequestSerializer, 
    MeetingRequestCreateSerializer,
    OfficeHoursSerializer
)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def meeting_request_list(request):
    """
    Get all meeting requests for the logged-in staff member.
    """
    # Ensure user is staff
    if request.user.role != 'staff':
        return Response(
            {'error': 'Only staff members can view meeting requests.'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    meeting_requests = MeetingRequest.objects.filter(staff=request.user)
    serializer = MeetingRequestSerializer(meeting_requests, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def meeting_request_accept(request, request_id):
    """
    Accept a meeting request.
    """
    meeting_request = get_object_or_404(MeetingRequest, id=request_id, staff=request.user)
    
    if meeting_request.status != MeetingRequest.Status.PENDING:
        return Response(
            {'error': 'This meeting request has already been processed.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    meeting_request.status = MeetingRequest.Status.ACCEPTED
    meeting_request.save()
    
    serializer = MeetingRequestSerializer(meeting_request)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def meeting_request_deny(request, request_id):
    """
    Deny a meeting request.
    """
    meeting_request = get_object_or_404(MeetingRequest, id=request_id, staff=request.user)
    
    if meeting_request.status != MeetingRequest.Status.PENDING:
        return Response(
            {'error': 'This meeting request has already been processed.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    meeting_request.status = MeetingRequest.Status.DENIED
    meeting_request.save()
    
    serializer = MeetingRequestSerializer(meeting_request)
    return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def office_hours_manage(request):
    """
    GET: Retrieve office hours for the logged-in staff member.
    POST: Create a new office hours block.
    """
    # Ensure user is staff
    if request.user.role != 'staff':
        return Response(
            {'error': 'Only staff members can manage office hours.'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    if request.method == 'GET':
        office_hours = OfficeHours.objects.filter(staff=request.user)
        serializer = OfficeHoursSerializer(office_hours, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        data = request.data.copy()
        data['staff'] = request.user.id
        serializer = OfficeHoursSerializer(data=data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def office_hours_delete(request, hours_id):
    """
    Delete an office hours block.
    """
    office_hours = get_object_or_404(OfficeHours, id=hours_id, staff=request.user)
    office_hours.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def meeting_request_create(request):
    """
    Create a new meeting request (for students).
    """
    data = request.data.copy()
    serializer = MeetingRequestCreateSerializer(data=data)
    
    if serializer.is_valid():
        # Set the student to the current user
        serializer.save(student=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
