from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from ..models import Ticket

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def email_webhook(request):
    # These keys depend on your email provider's format (e.g., SendGrid Inbound Parse)
    sender_email = request.data.get('from')
    subject = request.data.get('subject')
    body = request.data.get('text')
    
    # Logic to extract K-Number or other details from the subject/body
    # For now, we will create a ticket with available info
    try:
        Ticket.objects.create(
            name="Email User",
            surname="Pending",
            k_email=sender_email,
            type_of_issue=subject,
            additional_details=body,
            image=request.FILES.get('attachment1') # Mapping first attachment to image
        )
        return Response(status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=400)