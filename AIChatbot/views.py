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


def _get_genai_client():
    """Import and configure Gemini so missing package doesn't crash Django startup."""
    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise RuntimeError(
            "Gemini configuration error: GEMINI_API_KEY or google-generativeai is not available. "
            "Install the google-generativeai package and configure GEMINI_API_KEY to use AI chatbot features."
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

    # Per-user tickets (for the authenticated user)
    if user is not None and getattr(user, "is_authenticated", False):
        user_tickets = Ticket.objects.filter(user=user).order_by("-created_at")[:10]
        lines.append(
            f"This conversation is with user id={user.id}. "
            f"They currently have {user_tickets.count()} ticket(s) in the system."
        )
        if user_tickets.exists():
            lines.append("Their recent tickets are:")
            for t in user_tickets:
                lines.append(
                    f"- ID: {t.id}, Issue: {t.type_of_issue}, "
                    f"Status: {t.status}, Priority: {t.priority}, Department: {t.department}"
                )
        else:
            lines.append("They have no tickets yet.")
        lines.append("")  # blank line

    # Global sample of tickets (optional extra context)
    recent = Ticket.objects.all().order_by("-created_at")[:10]
    lines.append("Global context: some recent tickets in the system:")
    for t in recent:
        lines.append(
            f"- ID: {t.id}, Issue: {t.type_of_issue}, "
            f"Status: {t.status}, Priority: {t.priority}, Department: {t.department}"
        )

    return "\n".join(lines)


def _chat_with_gemini(messages, system_prompt=None, user=None):
    """
    Sends context + user messages to Gemini 1.5 Flash.
    messages: [{"role": "user"|"assistant", "content": "..."}, ...]
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set. Add it to .env or Heroku config vars.")

    genai = _get_genai_client()

    base_system = system_prompt or DEFAULT_SYSTEM
    context = _get_ticket_context(user=user)
    full_system = (
        f"{base_system}\n\n"
        "When the user says things like 'my tickets' or 'how many tickets I have', "
        "they mean the tickets listed in the 'This conversation is with user id=...' "
        "section of the context below.\n\n"
        f"{context}"
    )

    # Convert our format (user/assistant) to Gemini history (user/model)
    history = []
    for m in messages:
        role = m.get("role")
        content = (m.get("content") or "").strip()
        if not content:
            continue
        if role == "user":
            history.append({"role": "user", "parts": [content]})
        elif role == "assistant":
            history.append({"role": "model", "parts": [content]})

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
        user_message = (request.POST.get("message") or "").strip()
        if user_message:
            messages = list(messages)
            messages.append({"role": "user", "content": user_message})
            try:
                content = _chat_with_gemini(messages, user=request.user)
                messages.append({"role": "assistant", "content": content})
                error = None
            except Exception as e:
                logger.exception("Gemini chat error")
                err_msg = str(e).strip()
                if "GEMINI_API_KEY" in err_msg or "api_key" in err_msg.lower():
                    error = "Gemini API key not configured. Set GEMINI_API_KEY in .env or Heroku config."
                else:
                    error = err_msg or "Chat request failed."
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
        err_msg = str(e).strip()
        return Response(
            {
                "error": "Gemini service unavailable. Configure GEMINI_API_KEY and install google-generativeai.",
                "detail": err_msg or "Gemini runtime configuration error.",
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    except Exception as e:
        logger.exception("Gemini chat error")
        err_msg = str(e).strip()
        return Response(
            {"error": "Chat request failed.", "detail": err_msg},
            status=status.HTTP_502_BAD_GATEWAY,
        )
