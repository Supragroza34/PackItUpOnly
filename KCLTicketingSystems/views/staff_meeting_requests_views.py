from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta

from ..models.meeting_request import MeetingRequest
from ..models.office_hours import OfficeHours
from ..serializers import (
    MeetingRequestSerializer,
    MeetingRequestCreateSerializer,
    OfficeHoursSerializer
)

from ..utils import notify_staff_on_meeting_request, notify_student_on_meeting_response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def meeting_request_list(request):
    """
    Get all meeting requests for the logged-in staff member.
    This keeps the HTTP boundary centralized for the ticketing workflow.
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
    This keeps the HTTP boundary centralized for the ticketing workflow.
    """
    meeting_request = get_object_or_404(MeetingRequest, id=request_id, staff=request.user)
    
    if meeting_request.status != MeetingRequest.Status.PENDING:
        return Response(
            {'error': 'This meeting request has already been processed.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    meeting_request.status = MeetingRequest.Status.ACCEPTED
    meeting_request.save()

    notify_student_on_meeting_response(meeting_request, request.user)
    
    serializer = MeetingRequestSerializer(meeting_request)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def meeting_request_deny(request, request_id):
    """
    Deny a meeting request.
    This keeps the HTTP boundary centralized for the ticketing workflow.
    """
    meeting_request = get_object_or_404(MeetingRequest, id=request_id, staff=request.user)
    
    if meeting_request.status != MeetingRequest.Status.PENDING:
        return Response(
            {'error': 'This meeting request has already been processed.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    meeting_request.status = MeetingRequest.Status.DENIED
    meeting_request.save()

    notify_student_on_meeting_response(meeting_request, request.user)
    
    serializer = MeetingRequestSerializer(meeting_request)
    return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def office_hours_manage(request):
    """
    GET: Retrieve office hours for the logged-in staff member.
    POST: Create a new office hours block.
    This keeps the HTTP boundary centralized for the ticketing workflow.
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
    This keeps the HTTP boundary centralized for the ticketing workflow.
    """
    office_hours = get_object_or_404(OfficeHours, id=hours_id, staff=request.user)
    office_hours.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def staff_available_slots(request, staff_id):
    """
    Returns available 15-minute meeting slots for a staff member on a given date.
    Slots occupied by PENDING or ACCEPTED meeting requests are excluded.
    Query param: date=YYYY-MM-DD
    This keeps the HTTP boundary centralized for the ticketing workflow.
    """
    from django.utils import timezone as dj_timezone

    User = get_user_model()

    date_str = request.query_params.get('date')
    if not date_str:
        return Response({'error': 'date parameter required (YYYY-MM-DD).'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

    staff = get_object_or_404(User, id=staff_id, role='staff')
    day_name = selected_date.strftime('%A')

    office_hours_blocks = OfficeHours.objects.filter(staff=staff, day_of_week=day_name)
    if not office_hours_blocks.exists():
        return Response({'slots': []})

    current_tz = dj_timezone.get_current_timezone()
    now = dj_timezone.now()
    slot_duration = timedelta(minutes=15)

    all_slots = []
    for oh in office_hours_blocks:
        current_slot = dj_timezone.make_aware(
            datetime.combine(selected_date, oh.start_time), current_tz
        )
        end_dt = dj_timezone.make_aware(
            datetime.combine(selected_date, oh.end_time), current_tz
        )
        while current_slot + slot_duration <= end_dt:
            if current_slot > now:
                all_slots.append(current_slot)
            current_slot += slot_duration

    all_slots.sort()

    # Collect booked datetimes (PENDING or ACCEPTED) for this staff member
    booked = set(
        MeetingRequest.objects.filter(
            staff=staff,
            status__in=[MeetingRequest.Status.PENDING, MeetingRequest.Status.ACCEPTED]
        ).values_list('meeting_datetime', flat=True)
    )

    available = [slot.isoformat() for slot in all_slots if slot not in booked]

    return Response({'slots': available})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def meeting_request_create(request):
    """
    GET: List meeting requests for the current user (student).
    POST: Create a new meeting request (for students).
    This keeps the HTTP boundary centralized for the ticketing workflow.
    """
    if request.method == 'GET':
        meeting_requests = MeetingRequest.objects.filter(student=request.user)
        serializer = MeetingRequestSerializer(meeting_requests, many=True)
        return Response(serializer.data)

    # POST
    data = request.data.copy()

    data['student'] = request.user.id

    serializer = MeetingRequestCreateSerializer(data=data)
    
    if serializer.is_valid():
        # Set the student to the current user
        #serializer.save(student=request.user)
        meeting_request = serializer.save(student=request.user)

        notify_staff_on_meeting_request(meeting_request)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
