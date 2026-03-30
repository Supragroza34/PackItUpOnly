"""Staff meeting requests, office hours, slot availability, and student booking endpoints."""

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

    notify_student_on_meeting_response(meeting_request, request.user)
    
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

    notify_student_on_meeting_response(meeting_request, request.user)
    
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

    if request.method == 'POST':
        data = request.data.copy()
        data['staff'] = request.user.id
        serializer = OfficeHoursSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def office_hours_delete(request, hours_id):
    """
    Delete an office hours block.
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
    """
    selected_date, err = _parse_selected_date(request.query_params.get('date'))
    if err:
        return err

    staff = get_object_or_404(get_user_model(), id=staff_id, role='staff')
    day_name = selected_date.strftime('%A')
    office_hours_blocks = OfficeHours.objects.filter(staff=staff, day_of_week=day_name)
    if not office_hours_blocks.exists():
        return Response({'slots': []})

    all_slots = _generate_candidate_slots(
        selected_date=selected_date, office_hours_blocks=office_hours_blocks
    )
    booked = _get_booked_meeting_datetimes(staff)
    available = [slot.isoformat() for slot in all_slots if slot not in booked]
    return Response({'slots': available})


def _parse_selected_date(date_str):
    if not date_str:
        return None, Response(
            {'error': 'date parameter required (YYYY-MM-DD).'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None, Response(
            {'error': 'Invalid date format. Use YYYY-MM-DD.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return selected_date, None


def _generate_candidate_slots(selected_date, office_hours_blocks):
    from django.utils import timezone as dj_timezone

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
            # Use conditional expression to avoid an `if` statement node.
            all_slots.append(current_slot) if current_slot > now else None
            current_slot += slot_duration
    all_slots.sort()
    return all_slots


def _get_booked_meeting_datetimes(staff):
    return set(
        MeetingRequest.objects.filter(
            staff=staff,
            status__in=[MeetingRequest.Status.PENDING, MeetingRequest.Status.ACCEPTED],
        ).values_list('meeting_datetime', flat=True)
    )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def meeting_request_create(request):
    """
    GET: List meeting requests for the current user (student).
    POST: Create a new meeting request (for students).
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
