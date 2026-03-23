"""
AI Chatbot: Django-rendered chat page + optional JSON API.
Uses Google Gemini API with ticket context.
"""
import logging
import os

from django.conf import settings
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from KCLTicketingSystems.models import Ticket

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM = (
    "You are a helpful support assistant for students at KCL. "
    "Answer questions about the ticketing system, FAQs, and general study support briefly and clearly."
)

SESSION_KEY_MESSAGES = "ai_chatbot_messages"
SESSION_KEY_ERROR = "ai_chatbot_error"


def _is_leaked_or_blocked_key_error(message: str) -> bool:
    msg = (message or "").lower()
    return (
        "api key was reported as leaked" in msg
        or "permissiondenied" in msg
        or "403" in msg and "api key" in msg
    )


def _format_ticket_line(ticket):
    return (
        f"- ID: {ticket.id}, Issue: {ticket.type_of_issue}, "
        f"Status: {ticket.status}, Priority: {ticket.priority}, Department: {ticket.department}"
    )


def _build_user_ticket_context_lines(user):
    lines = []
    user_tickets = Ticket.objects.filter(user=user).order_by("-created_at")[:10]
    lines.append(
        f"This conversation is with user id={user.id}. "
        f"They currently have {user_tickets.count()} ticket(s) in the system."
    )
    if user_tickets.exists():
        lines.append("Their recent tickets are:")
        lines.extend(_format_ticket_line(ticket) for ticket in user_tickets)
    else:
        lines.append("They have no tickets yet.")
    lines.append("")
    return lines


def _build_global_ticket_context_lines():
    lines = ["Global context: some recent tickets in the system:"]
    recent = Ticket.objects.all().order_by("-created_at")[:10]
    lines.extend(_format_ticket_line(ticket) for ticket in recent)
    return lines


def _normalize_messages_to_gemini_history(messages):
    role_map = {"user": "user", "assistant": "model"}
    history = []
    for message in messages:
        gemini_role = role_map.get(message.get("role"))
        content = (message.get("content") or "").strip()
        if not content or not gemini_role:
            continue
        history.append({"role": gemini_role, "parts": [content]})
    return history


def _require_gemini_api_key():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set. Add it to .env or Heroku config vars.")
    return api_key


def _build_full_system_prompt(system_prompt, user):
    base_system = system_prompt or DEFAULT_SYSTEM
    context = _get_ticket_context(user=user)
    return (
        f"{base_system}\n\n"
        "When the user says things like 'my tickets' or 'how many tickets I have', "
        "they mean the tickets listed in the 'This conversation is with user id=...' "
        "section of the context below.\n\n"
        f"{context}"
    )


def _chat_page_error_message(exception):
    err_msg = str(exception).strip()
    if "GEMINI_API_KEY" in err_msg or "api_key" in err_msg.lower():
        return "Gemini API key not configured. Set GEMINI_API_KEY in .env or Heroku config."
    if _is_leaked_or_blocked_key_error(err_msg):
        return (
            "Gemini API key is blocked (reported leaked). "
            "Create a new key in Google AI Studio/Cloud, update GEMINI_API_KEY, then restart the server."
        )
    return err_msg or "Chat request failed."


def _handle_chat_page_post(request, messages):
    user_message = (request.POST.get("message") or "").strip()
    if not user_message:
        return messages, None

    updated_messages = list(messages)
    updated_messages.append({"role": "user", "content": user_message})
    try:
        content = _chat_with_gemini(updated_messages, user=request.user)
        updated_messages.append({"role": "assistant", "content": content})
        return updated_messages, None
    except Exception as exc:
        logger.exception("Gemini chat error")
        return updated_messages, _chat_page_error_message(exc)


def _api_error_response(err_msg):
    if _is_leaked_or_blocked_key_error(err_msg):
        return Response(
            {
                "error": "Gemini API key is blocked (reported leaked).",
                "detail": "Create a new Gemini key, update GEMINI_API_KEY, and restart the backend process.",
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return Response(
        {"error": "Chat request failed.", "detail": err_msg},
        status=status.HTTP_502_BAD_GATEWAY,
    )


def _get_genai_client():
    """Import and configure Gemini so missing package doesn't crash Django startup."""
    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise RuntimeError(
            "google-generativeai is not installed. Install requirements to use AI chatbot features."
        ) from exc

    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
    return genai


def _get_ticket_context(user=None):
    """
    Build context about this user's tickets plus a small global sample.
    This helps Gemini answer questions like 'how many tickets do I have?'.
    """
    lines = []
    if user is not None and getattr(user, "is_authenticated", False):
        lines.extend(_build_user_ticket_context_lines(user))
    lines.extend(_build_global_ticket_context_lines())
    return "\n".join(lines)


def _chat_with_gemini(messages, system_prompt=None, user=None):
    """
    Sends context + user messages to Gemini 1.5 Flash.
    messages: [{"role": "user"|"assistant", "content": "..."}, ...]
    """
    _require_gemini_api_key()
    genai = _get_genai_client()
    full_system = _build_full_system_prompt(system_prompt, user)
    history = _normalize_messages_to_gemini_history(messages)

    if not history or history[-1]["role"] != "user":
        raise ValueError("At least one user message required.")

    # Last message is the new user input; history is everything before
    new_user_message = history[-1]["parts"][0]
    chat_history = history[:-1]

    model = genai.GenerativeModel(
        model_name="gemini-flash-latest",
        system_instruction=full_system,
    )
    chat = model.start_chat(history=chat_history)
    response = chat.send_message(new_user_message)
    return (response.text or "").strip()


@require_http_methods(["GET", "POST"])
def chat_page(request):
    """Django-rendered chatbot: GET shows form + history, POST sends message and re-renders."""
    messages = request.session.get(SESSION_KEY_MESSAGES, [])
    error = request.session.pop(SESSION_KEY_ERROR, None)

    if request.method == "POST":
        messages, error = _handle_chat_page_post(request, messages)
        request.session[SESSION_KEY_MESSAGES] = messages
        if error:
            request.session[SESSION_KEY_ERROR] = error
        return redirect("chat_page")

    return render(
        request,
        "ai_chatbot/chat.html",
        {"messages": messages, "error": error, "frontend_url": getattr(settings, "FRONTEND_URL", "http://localhost:3000")},
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat(request):
    """
    POST body: { "messages": [ {"role": "user"|"assistant", "content": "..."}, ... ] }
    Optionally: "system": "optional system prompt"
    Returns: { "message": { "role": "assistant", "content": "..." } }
    """
    messages = request.data.get("messages")
    if not messages or not isinstance(messages, list):
        return Response(
            {"error": "Request must include a non-empty 'messages' array."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    system_prompt = request.data.get("system") or DEFAULT_SYSTEM

    try:
        content = _chat_with_gemini(messages, system_prompt=system_prompt, user=request.user)
        return Response({"message": {"role": "assistant", "content": content}})
    except RuntimeError as e:
        if "GEMINI_API_KEY" in str(e):
            return Response(
                {"error": "GEMINI_API_KEY not configured. Set it in .env or Heroku config vars."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        raise
    except Exception as e:
        logger.exception("Gemini chat error")
        err_msg = str(e).strip()
        return _api_error_response(err_msg)
