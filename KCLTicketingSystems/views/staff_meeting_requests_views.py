from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def meeting_request_list(request):
    meeting_requests = []
    return Response(meeting_requests)