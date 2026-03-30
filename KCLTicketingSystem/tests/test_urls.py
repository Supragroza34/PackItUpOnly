"""Tests for root URL routing."""

from django.test import SimpleTestCase
from django.urls import resolve, reverse
from KCLTicketingSystem import urls as project_urls

class ProjectURLTests(SimpleTestCase):
    def test_home_url_resolves(self):
        resolver = resolve('/')
        self.assertEqual(resolver.view_name, 'home')

    def test_admin_url_resolves(self):
        resolver = resolve('/admin/')
        self.assertEqual(resolver.app_name, 'admin')

    def test_chat_url_resolves(self):
        resolver = resolve('/chat/')
        self.assertEqual(resolver.view_name, 'chat_page')

    def test_ticket_form_url_resolves(self):
        resolver = resolve('/ticket-form/')
        self.assertEqual(resolver.view_name, 'ticket_form')

    def test_api_submit_ticket_url_resolves(self):
        resolver = resolve('/api/submit-ticket/')
        self.assertEqual(resolver.view_name, 'submit_ticket')

    def test_reverse_home(self):
        url = reverse('home')
        self.assertEqual(url, '/')

    def test_reverse_chat(self):
        url = reverse('chat_page')
        self.assertEqual(url, '/chat/')
