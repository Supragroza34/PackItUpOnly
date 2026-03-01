"""
AI Chatbot: Django-rendered chat page + optional JSON API.
Uses Ollama (e.g. ollama run llama2).
"""
import logging
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM = (
    "You are a helpful support assistant for students at KCL. "
    "Answer questions about the ticketing system, FAQs, and general study support briefly and clearly."
)

SESSION_KEY_MESSAGES = "ai_chatbot_messages"
SESSION_KEY_ERROR = "ai_chatbot_error"


def _chat_with_ollama(messages, model="llama2", system_prompt=None):
    """Call Ollama with message list; return assistant content or raise."""
    try:
        import ollama
    except ImportError:
        raise RuntimeError("Ollama package not installed.")
    system_prompt = system_prompt or DEFAULT_SYSTEM
    ollama_messages = [{"role": "system", "content": system_prompt}]
    for m in messages:
        role = m.get("role")
        content = m.get("content")
        if role in ("user", "assistant") and content is not None:
            ollama_messages.append({"role": role, "content": str(content).strip()})
    if len(ollama_messages) <= 1:
        raise ValueError("At least one user message required.")
    response = ollama.chat(model=model, messages=ollama_messages)
    reply = response.get("message") or {}
    return (reply.get("content") or "").strip()


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
                content = _chat_with_ollama(messages)
                messages.append({"role": "assistant", "content": content})
                error = None
            except Exception as e:
                logger.exception("Ollama chat error")
                err_msg = str(e).strip()
                if "connection" in err_msg.lower() or "refused" in err_msg.lower():
                    error = "Cannot reach Ollama. Start Ollama and run a model (e.g. ollama run llama2)."
                else:
                    error = err_msg or "Chat request failed."
            request.session[SESSION_KEY_MESSAGES] = messages
            if error:
                request.session[SESSION_KEY_ERROR] = error
        return redirect("chat_page")

    return render(request, "ai_chatbot/chat.html", {"messages": messages, "error": error})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat(request):
    """
    POST body: { "messages": [ {"role": "user"|"assistant", "content": "..."}, ... ] }
    Optionally: "model": "llama2" (default), "system": "optional system prompt"
    Returns: { "message": { "role": "assistant", "content": "..." } }
    """
    messages = request.data.get("messages")
    if not messages or not isinstance(messages, list):
        return Response(
            {"error": "Request must include a non-empty 'messages' array."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    model = request.data.get("model") or "llama2"
    system_prompt = request.data.get("system") or DEFAULT_SYSTEM

    try:
        content = _chat_with_ollama(messages, model=model, system_prompt=system_prompt)
        return Response({"message": {"role": "assistant", "content": content}})
    except RuntimeError as e:
        if "not installed" in str(e).lower():
            return Response(
                {"error": "Ollama package not installed. Add 'ollama' to requirements.txt and install."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        raise
    except Exception as e:
        logger.exception("Ollama chat error")
        err_msg = str(e).strip()
        if "connection" in err_msg.lower() or "refused" in err_msg.lower():
            return Response(
                {
                    "error": "Cannot reach Ollama. Start Ollama and pull a model (e.g. ollama run llama2).",
                    "detail": err_msg,
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(
            {"error": "Chat request failed.", "detail": err_msg},
            status=status.HTTP_502_BAD_GATEWAY,
        )
