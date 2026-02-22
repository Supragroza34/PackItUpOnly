import json
import logging
import os
import re

logger = logging.getLogger(__name__)

# noqa: PLR0915
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


def extract_ticket_info_with_ai(email_content, sender_email):
    prompt = _build_prompt(email_content)
    data = _try_gemini(prompt, sender_email)
    if data:
        return data
    data = _try_openai(prompt, sender_email)
    if data:
        return data
    logger.info("Using fallback regex extraction (no AI available)")
    return fallback_extraction(email_content, sender_email)


def _build_prompt(email_content):
    return f"""
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


def _try_gemini(prompt, sender_email):
    client = _get_gemini_client()
    if not client:
        return None
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash-latest",
            contents=_gemini_prompt(prompt),
        )
        text = _clean_gemini_response(response.text)
        data = json.loads(text)
        return validate_extracted_data(data, sender_email)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gemini extraction failed: %s", exc)
        return None


def _get_gemini_client():
    if not GEMINI_AVAILABLE:
        return None
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        return None
    return genai.Client(api_key=gemini_key)


def _gemini_prompt(prompt):
    return (
        "You are a helpful assistant that extracts structured data from emails. "
        "Always return valid JSON only.\n\n"
        f"{prompt}"
    )


def _clean_gemini_response(text):
    cleaned = text.strip()
    if not cleaned.startswith("```"):
        return cleaned
    parts = cleaned.split("```", 2)
    body = parts[1] if len(parts) > 1 else cleaned
    body = body.lstrip()
    if body.startswith("json"):
        body = body[4:]
    return body.strip()


def _try_openai(prompt, sender_email):
    client = _openai_client()
    if not client:
        return None
    try:
        response = client.chat.completions.create(**_openai_kwargs(prompt))
        content = response.choices[0].message.content
        data = json.loads(content)
        return validate_extracted_data(data, sender_email)
    except Exception as exc:  # noqa: BLE001
        logger.warning("OpenAI extraction failed: %s", exc)
        return None


def _openai_client():
    if not OPENAI_AVAILABLE:
        return None
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return openai.OpenAI(api_key=api_key)


def _openai_kwargs(prompt):
    return {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant that extracts structured data "
                    "from emails. Always return valid JSON only."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }


def validate_extracted_data(data, sender_email):
    data = dict(data or {})
    _ensure_k_number(data, sender_email)
    _ensure_k_email(data, sender_email)
    _ensure_department(data)
    _clean_names(data)
    _ensure_defaults(data)
    return data


def _ensure_k_number(data, sender_email):
    match = re.search(r"K(\d+)@kcl\.ac\.uk", sender_email)
    if match and not data.get("k_number"):
        data["k_number"] = match.group(1)
    if data.get("k_number") and data["k_number"] != "00000000":
        return
    body = data.get("additional_details", "")
    body_match = re.search(r"K(\d{8})", body)
    if body_match:
        data["k_number"] = body_match.group(1)


def _ensure_k_email(data, sender_email):
    k_number = data.get("k_number")
    email = data.get("k_email", "")
    if email and re.match(r"K\d+@kcl\.ac\.uk", email):
        return
    if k_number and k_number != "00000000":
        data["k_email"] = f"K{k_number}@kcl.ac.uk"
    else:
        data["k_email"] = sender_email


def _ensure_department(data):
    valid_departments = ["Informatics", "Engineering", "Medicine"]
    department = data.get("department")
    if department in valid_departments:
        return
    data["department"] = "Informatics"


def _clean_names(data):
    name = re.sub(r"\d", "", data.get("name", "Email User")).strip()
    surname = re.sub(r"\d", "", data.get("surname", "Pending")).strip()
    data["name"] = name if name else "Email User"
    data["surname"] = surname if surname else "Pending"


def _ensure_defaults(data):
    data["k_number"] = data.get("k_number", "00000000").strip()
    data["type_of_issue"] = data.get("type_of_issue", "General Issue").strip()
    data["additional_details"] = data.get("additional_details", "").strip()


def fallback_extraction(email_content, sender_email):
    k_number = _fallback_k_number(email_content, sender_email)
    name, surname = _fallback_name(email_content)
    department = _fallback_department(email_content)
    issue = _fallback_issue(email_content)
    return _fallback_payload(
        email_content, sender_email, k_number, name, surname, department, issue
    )


def _fallback_k_number(email_content, sender_email):
    match = re.search(r"K(\d+)@kcl\.ac\.uk", sender_email)
    if match:
        return match.group(1)
    body_match = re.search(r"K(\d{8})", email_content)
    return body_match.group(1) if body_match else "00000000"


def _fallback_name(email_content):
    name = "Email User"
    surname = "Pending"
    for line in email_content.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith(
            ("subject:", "from:", "to:", "sent:", "re:", "fw:", "fwd:")
        ):
            continue
        match = re.match(r"^([A-Z][a-z]+)\s+([A-Z][a-z]+)$", stripped)
        if match and _valid_name_parts(match.group(1), match.group(2)):
            return match.group(1), match.group(2)
    return _fallback_name_from_body(email_content, name, surname)


def _valid_name_parts(first, last):
    if re.search(r"\d", first) or re.search(r"\d", last):
        return False
    return True


def _fallback_name_from_body(email_content, default_name, default_surname):
    pattern = r"([A-Z][a-z]+)\s+([A-Z][a-z]+)"
    match = re.search(pattern, email_content)
    if not match:
        return default_name, default_surname
    first, last = match.group(1), match.group(2)
    if not _valid_name_parts(first, last):
        return default_name, default_surname
    return first, last


def _fallback_department(email_content):
    if re.search(r"(?i)(informatics|computer science|cs)", email_content):
        return "Informatics"
    if re.search(r"(?i)(engineering)", email_content):
        return "Engineering"
    if re.search(r"(?i)(medicine|medical)", email_content):
        return "Medicine"
    return "Informatics"


def _fallback_issue(email_content):
    subject_match = re.search(r"Subject:\s*(.+?)(?:\n|$)", email_content)
    if not subject_match:
        return "General Issue"
    return subject_match.group(1).strip() or "General Issue"


def _fallback_payload(
    email_content,
    sender_email,
    k_number,
    name,
    surname,
    department,
    issue,
):
    email = sender_email
    if k_number != "00000000":
        email = f"K{k_number}@kcl.ac.uk"
    return {
        "name": name,
        "surname": surname,
        "k_number": k_number,
        "k_email": email,
        "department": department,
        "type_of_issue": issue,
        "additional_details": email_content,
    }

