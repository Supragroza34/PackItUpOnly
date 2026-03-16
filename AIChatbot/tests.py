import builtins
import sys
import types

from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

from . import views


User = get_user_model()


class AIChatbotAPITest(TestCase):
    """Tests for the JSON AI chat API."""

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/ai-chatbot/chat/"
        self.user = User.objects.create_user(
            username="student",
            email="student@test.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)

    def test_chat_requires_messages_array(self):
        """Missing or invalid messages payload should return 400."""
        resp = self.client.post(self.url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", resp.data)

    def test_chat_requires_authentication(self):
        """Endpoint is protected by IsAuthenticated."""
        anon_client = APIClient()
        resp = anon_client.post(
            self.url,
            {"messages": [{"role": "user", "content": "Hi"}]},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("AIChatbot.views._chat_with_ollama")
    def test_chat_returns_assistant_message(self, mock_chat):
        """Successful call returns assistant message content."""
        mock_chat.return_value = "Hello, how can I help you?"

        payload = {
            "messages": [
                {"role": "user", "content": "Hi"},
            ]
        }
        resp = self.client.post(self.url, payload, format="json")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("message", resp.data)
        self.assertEqual(
            resp.data["message"]["content"],
            "Hello, how can I help you?",
        )
        mock_chat.assert_called_once()

    @patch("AIChatbot.views._chat_with_ollama")
    def test_chat_passes_model_and_system_prompt(self, mock_chat):
        """Provided model and system prompt are passed through."""
        mock_chat.return_value = "OK"
        payload = {
            "messages": [{"role": "user", "content": "Hi"}],
            "model": "llama3.1",
            "system": "You are custom.",
        }

        resp = self.client.post(self.url, payload, format="json")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        mock_chat.assert_called_once_with(
            payload["messages"],
            model="llama3.1",
            system_prompt="You are custom.",
        )

    @patch("AIChatbot.views._chat_with_ollama")
    def test_chat_runtime_not_installed_maps_to_503(self, mock_chat):
        """Runtime import issue returns service unavailable guidance."""
        mock_chat.side_effect = RuntimeError("Ollama package not installed.")

        resp = self.client.post(
            self.url,
            {"messages": [{"role": "user", "content": "Hi"}]},
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn("Ollama package not installed", resp.data["error"])

    @patch("AIChatbot.views._chat_with_ollama")
    def test_chat_connection_error_maps_to_503(self, mock_chat):
        """Connection/refused errors map to service unavailable."""
        mock_chat.side_effect = Exception("Connection refused")

        resp = self.client.post(
            self.url,
            {"messages": [{"role": "user", "content": "Hi"}]},
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn("Cannot reach Ollama", resp.data["error"])
        self.assertIn("detail", resp.data)

    @patch("AIChatbot.views._chat_with_ollama")
    def test_chat_generic_error_maps_to_502(self, mock_chat):
        """Non-connection failures map to bad gateway."""
        mock_chat.side_effect = Exception("something failed")

        resp = self.client.post(
            self.url,
            {"messages": [{"role": "user", "content": "Hi"}]},
            format="json",
        )

        self.assertEqual(resp.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(resp.data["error"], "Chat request failed.")
        self.assertEqual(resp.data["detail"], "something failed")


class AIChatbotPageTest(TestCase):
    """Tests for the Django-rendered chat page."""

    def test_get_chat_page_renders(self):
        resp = self.client.get("/chat/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "AI Helper")

    @patch("AIChatbot.views._chat_with_ollama")
    def test_post_chat_page_appends_messages(self, mock_chat):
        """Posting a message appends user and assistant messages to the page."""
        mock_chat.return_value = "Assistant reply"

        resp = self.client.post("/chat/", {"message": "Hello"}, follow=True)

        self.assertEqual(resp.status_code, 200)
        # User message should be shown
        self.assertContains(resp, "Hello")
        # Assistant reply should also be shown
        self.assertContains(resp, "Assistant reply")

    @patch("AIChatbot.views._chat_with_ollama")
    def test_post_empty_message_skips_chat_call(self, mock_chat):
        """Blank message should redirect without calling Ollama."""
        resp = self.client.post("/chat/", {"message": "   "})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse("chat_page"))
        mock_chat.assert_not_called()

    @patch("AIChatbot.views._chat_with_ollama")
    def test_post_chat_page_connection_error_message(self, mock_chat):
        """Connection errors are converted to a friendly message on page."""
        mock_chat.side_effect = Exception("Connection refused")

        resp = self.client.post("/chat/", {"message": "Hello"}, follow=True)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Cannot reach Ollama")
        self.assertContains(resp, "Hello")

    @patch("AIChatbot.views._chat_with_ollama")
    def test_post_chat_page_generic_error_message(self, mock_chat):
        """Generic failures display the backend error text."""
        mock_chat.side_effect = Exception("backend boom")

        resp = self.client.post("/chat/", {"message": "Hello"}, follow=True)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "backend boom")


class ChatWithOllamaHelperTest(TestCase):
    """Unit tests for _chat_with_ollama message normalization and errors."""

    def test_helper_builds_messages_and_strips_content(self):
        captured = {}

        class FakeClient:
            def __init__(self, timeout):
                captured["timeout"] = timeout

            def chat(self, model, messages):
                captured["model"] = model
                captured["messages"] = messages
                return {"message": {"content": "  Reply text  "}}

        fake_ollama = types.SimpleNamespace(Client=FakeClient)
        with patch.dict(sys.modules, {"ollama": fake_ollama}):
            content = views._chat_with_ollama(
                [
                    {"role": "ignored", "content": "nope"},
                    {"role": "user", "content": "  Hi  "},
                    {"role": "assistant", "content": "  Previous  "},
                    {"role": "user", "content": None},
                ],
                model="llama3.2",
            )

        self.assertEqual(content, "Reply text")
        self.assertEqual(captured["timeout"], 120.0)
        self.assertEqual(captured["model"], "llama3.2")
        self.assertEqual(captured["messages"][0]["role"], "system")
        self.assertEqual(captured["messages"][1], {"role": "user", "content": "Hi"})
        self.assertEqual(
            captured["messages"][2],
            {"role": "assistant", "content": "Previous"},
        )

    def test_helper_requires_at_least_one_user_or_assistant_message(self):
        class FakeClient:
            def __init__(self, timeout):
                pass

            def chat(self, model, messages):
                return {"message": {"content": "unused"}}

        fake_ollama = types.SimpleNamespace(Client=FakeClient)
        with patch.dict(sys.modules, {"ollama": fake_ollama}):
            with self.assertRaises(ValueError):
                views._chat_with_ollama([{"role": "system", "content": "Only system"}])

    def test_helper_raises_runtime_error_when_ollama_not_installed(self):
        original_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "ollama":
                raise ImportError("No module named ollama")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import):
            with self.assertRaises(RuntimeError):
                views._chat_with_ollama([{"role": "user", "content": "Hi"}])

