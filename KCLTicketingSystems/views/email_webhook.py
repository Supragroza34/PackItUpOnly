from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from ..models import Ticket
import os
import re
import json
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Try to import AI libraries (fallback if not available)
try:
    import openai
    openai.api_key = os.getenv('OPENAI_API_KEY', '')
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def email_webhook(request):
    """
    Webhook endpoint that receives emails and uses AI to extract ticket information
    """
    # Log incoming request data for debugging
    logger.info("=" * 50)
    logger.info("Email webhook called")
    logger.info(f"Request data keys: {list(request.data.keys())}")
    logger.info(f"Request FILES keys: {list(request.FILES.keys())}")
    
    sender_email = request.data.get('from', '')
    subject = request.data.get('subject', '')
    body = request.data.get('text', '') or request.data.get('body-plain', '')
    
    logger.info(f"From: {sender_email}")
    logger.info(f"Subject: {subject}")
    logger.info(f"Body length: {len(body)} characters")
    
    # Combine email content for AI parsing
    email_content = f"""
    Subject: {subject}
    
    From: {sender_email}
    
    Body:
    {body}
    """
    
    # Use AI to extract structured information
    logger.info("Extracting ticket info with AI...")
    extracted_data = extract_ticket_info_with_ai(email_content, sender_email)
    logger.info(f"Extracted data: {json.dumps(extracted_data, indent=2)}")
    
    try:
        # Create the ticket (users can now have multiple tickets)
        k_number = extracted_data.get('k_number', '')
        logger.info(f"Creating ticket for K-Number: {k_number}")
        
        # Create the ticket
        logger.info("Creating ticket...")
        ticket = Ticket.objects.create(
            name=extracted_data.get('name', 'Email User'),
            surname=extracted_data.get('surname', 'Pending'),
            k_number=extracted_data.get('k_number', '00000000'),
            k_email=extracted_data.get('k_email', sender_email),
            department=extracted_data.get('department', 'Informatics'),
            type_of_issue=extracted_data.get('type_of_issue', subject),
            additional_details=extracted_data.get('additional_details', body),
        )
        
        logger.info(f"✅ Ticket created successfully! ID: {ticket.id}")
        return Response({
            'message': 'Ticket created successfully',
            'ticket_id': ticket.id,
            'extracted_data': extracted_data
        }, status=200)
    except Exception as e:
        logger.error(f"❌ Error creating ticket: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return Response({
            'error': str(e),
            'error_type': type(e).__name__,
            'extracted_data': extracted_data
        }, status=400)


def extract_ticket_info_with_ai(email_content, sender_email):
    """
    Use AI to extract structured ticket information from email
    """
    prompt = f"""
    Extract ticket information from this email and return it as JSON.
    
    Email content:
    {email_content}
    
    Extract the following fields:
    - name: First name (no numbers, required)
    - surname: Last name (no numbers, required)
    - k_number: K-Number (8 digits, numbers only, extract from email address or body)
    - k_email: Email address (should match K{{number}}@kcl.ac.uk format)
    - department: One of ["Informatics", "Engineering", "Medicine"] (required)
    - type_of_issue: Type of issue/problem (required)
    - additional_details: Full description/details (required)
    
    Rules:
    1. Extract K-Number from email address if it matches K[number]@kcl.ac.uk pattern
    2. If K-Number not in email, try to find it in the body text (look for "K" followed by 8 digits)
    3. If name/surname not found in email, use "Email User" and "Pending"
    4. Department must be one of: Informatics, Engineering, or Medicine
    5. If department not found, default to "Informatics"
    6. Return valid JSON only, no other text
    
    Return JSON format:
    {{
        "name": "...",
        "surname": "...",
        "k_number": "...",
        "k_email": "...",
        "department": "...",
        "type_of_issue": "...",
        "additional_details": "..."
    }}
    """
    
    # Try Gemini first (free tier), then OpenAI, then fallback
    try:
        # Try Google Gemini (free tier available) - using new google.genai API
        if GEMINI_AVAILABLE:
            gemini_key = os.getenv('GEMINI_API_KEY')
            if gemini_key:
                logger.info("Using Google Gemini for extraction...")
                try:
                    # Initialize client with API key
                    client = genai.Client(api_key=gemini_key)
                    
                    # Try different models in order of preference
                    models_to_try = [
                        "gemini-2.0-flash-exp",
                        "gemini-1.5-flash-latest",
                        "gemini-1.5-flash",
                        "gemini-1.5-pro",
                        "gemini-pro"
                    ]
                    
                    full_prompt = f"You are a helpful assistant that extracts structured data from emails. Always return valid JSON only.\n\n{prompt}"
                    
                    response = None
                    for model_name in models_to_try:
                        try:
                            logger.info(f"Trying Gemini model: {model_name}")
                            response = client.models.generate_content(
                                model=model_name,
                                contents=full_prompt
                            )
                            break  # Success, exit loop
                        except Exception as e:
                            logger.warning(f"Model {model_name} failed: {e}")
                            continue
                    
                    if not response:
                        raise Exception("All Gemini models failed")
                    
                    # Extract JSON from response
                    response_text = response.text.strip()
                    # Remove markdown code blocks if present
                    if response_text.startswith('```'):
                        response_text = response_text.split('```')[1]
                        if response_text.startswith('json'):
                            response_text = response_text[4:]
                    response_text = response_text.strip()
                    
                    extracted_json = json.loads(response_text)
                    return validate_extracted_data(extracted_json, sender_email)
                except Exception as e:
                    raise Exception(f"Gemini API error: {str(e)}")
    except Exception as e:
        logger.warning(f"Gemini extraction failed: {e}")
    
    # Try OpenAI as fallback
    try:
        if OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                logger.info("Using OpenAI for extraction...")
                client = openai.OpenAI(api_key=api_key)
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that extracts structured data from emails. Always return valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                
                extracted_json = json.loads(response.choices[0].message.content)
                return validate_extracted_data(extracted_json, sender_email)
    except Exception as e:
        logger.warning(f"OpenAI extraction failed: {e}")
    
    # Fallback to regex extraction
    logger.info("Using fallback regex extraction (no AI available)")
    return fallback_extraction(email_content, sender_email)


def validate_extracted_data(data, sender_email):
    """
    Validate and clean extracted data
    """
    # Extract K-Number from email if not found
    k_number_match = re.search(r'K(\d+)@kcl\.ac\.uk', sender_email)
    if k_number_match and not data.get('k_number'):
        data['k_number'] = k_number_match.group(1)
    
    # Extract K-Number from body if still not found
    if not data.get('k_number') or data.get('k_number') == '00000000':
        k_number_in_body = re.search(r'K(\d{8})', data.get('additional_details', ''))
        if k_number_in_body:
            data['k_number'] = k_number_in_body.group(1)
    
    # Ensure K-email matches format
    if not data.get('k_email') or not re.match(r'K\d+@kcl\.ac\.uk', data.get('k_email', '')):
        if data.get('k_number') and data.get('k_number') != '00000000':
            data['k_email'] = f"K{data['k_number']}@kcl.ac.uk"
        else:
            data['k_email'] = sender_email
    
    # Validate department
    valid_departments = ['Informatics', 'Engineering', 'Medicine']
    if data.get('department') not in valid_departments:
        data['department'] = 'Informatics'  # Default
    
    # Clean name and surname (remove numbers)
    name = re.sub(r'\d', '', data.get('name', 'Email User')).strip()
    surname = re.sub(r'\d', '', data.get('surname', 'Pending')).strip()
    
    # Ensure required fields have defaults
    data['name'] = name if name else 'Email User'
    data['surname'] = surname if surname else 'Pending'
    data['k_number'] = data.get('k_number', '00000000').strip()
    data['type_of_issue'] = data.get('type_of_issue', 'General Issue').strip()
    data['additional_details'] = data.get('additional_details', '').strip()
    
    return data


def fallback_extraction(email_content, sender_email):
    """
    Fallback extraction using regex if AI fails
    """
    # Extract K-Number from email
    k_number_match = re.search(r'K(\d+)@kcl\.ac\.uk', sender_email)
    k_number = k_number_match.group(1) if k_number_match else '00000000'
    
    # Try to extract from body
    if k_number == '00000000':
        k_number_in_body = re.search(r'K(\d{8})', email_content)
        if k_number_in_body:
            k_number = k_number_in_body.group(1)
    
    # Try to extract name from email body (look for patterns like "Amey Tripathi" or "John Smith")
    name = 'Email User'
    surname = 'Pending'
    
    # Heuristic 1: scan line-by-line for a clean full name line
    for line in email_content.splitlines():
        stripped = line.strip()
        # Skip header lines
        if stripped.lower().startswith(('subject:', 'from:', 'to:', 'sent:', 're:', 'fw:', 'fwd:')):
            continue
        # Match a line that looks like "Amey Tripathi"
        m = re.match(r'^([A-Z][a-z]+)\s+([A-Z][a-z]+)$', stripped)
        if m:
            candidate_name, candidate_surname = m.group(1), m.group(2)
            if not re.search(r'\d', candidate_name) and not re.search(r'\d', candidate_surname):
                name = candidate_name
                surname = candidate_surname
                break

    # Heuristic 2: if still default, fall back to first capitalised pair anywhere in body
    if name == 'Email User' and surname == 'Pending':
        name_pattern = r'([A-Z][a-z]+)\s+([A-Z][a-z]+)'
        name_match = re.search(name_pattern, email_content)
        if name_match:
            candidate_name = name_match.group(1)
            candidate_surname = name_match.group(2)
            if not re.search(r'\d', candidate_name) and not re.search(r'\d', candidate_surname):
                name = candidate_name
                surname = candidate_surname
    
    # Try to extract department from body
    department = 'Informatics'  # Default
    if re.search(r'(?i)(informatics|computer science|cs)', email_content):
        department = 'Informatics'
    elif re.search(r'(?i)(engineering)', email_content):
        department = 'Engineering'
    elif re.search(r'(?i)(medicine|medical)', email_content):
        department = 'Medicine'
    
    # Extract subject/issue type from email
    subject_match = re.search(r'Subject:\s*(.+?)(?:\n|$)', email_content)
    type_of_issue = subject_match.group(1).strip() if subject_match else 'General Issue'
    
    return {
        'name': name,
        'surname': surname,
        'k_number': k_number,
        'k_email': f"K{k_number}@kcl.ac.uk" if k_number != '00000000' else sender_email,
        'department': department,
        'type_of_issue': type_of_issue,
        'additional_details': email_content
    }
