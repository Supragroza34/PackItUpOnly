from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model


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

    @patch("AIChatbot.views._chat_with_gemini")
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


class AIChatbotPageTest(TestCase):
    """Tests for the Django-rendered chat page."""

    def test_get_chat_page_renders(self):
        resp = self.client.get("/chat/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "AI Helper")

    @patch("AIChatbot.views._chat_with_gemini")
    def test_post_chat_page_appends_messages(self, mock_chat):
        """Posting a message appends user and assistant messages to the page."""
        mock_chat.return_value = "Assistant reply"

        resp = self.client.post("/chat/", {"message": "Hello"}, follow=True)

        self.assertEqual(resp.status_code, 200)
        # User message should be shown
        self.assertContains(resp, "Hello")
        # Assistant reply should also be shown
        self.assertContains(resp, "Assistant reply")

