"""Tests for Django project settings configuration."""

import os
import importlib
from django.test import TestCase, override_settings
from django.conf import settings

class SettingsTest(TestCase):
    def test_secret_key_is_set(self):
        self.assertTrue(hasattr(settings, 'SECRET_KEY'))
        self.assertTrue(settings.SECRET_KEY)

    def test_debug_flag(self):
        self.assertIsInstance(settings.DEBUG, bool)

    def test_allowed_hosts(self):
        self.assertIn('localhost', settings.ALLOWED_HOSTS)
        self.assertIn('127.0.0.1', settings.ALLOWED_HOSTS)

    def test_env_loading(self):
        # Simulate .env variable
        os.environ['TEST_ENV_VAR'] = 'test_value'
        importlib.reload(settings)
        self.assertEqual(os.getenv('TEST_ENV_VAR'), 'test_value')

    def test_installed_apps(self):
        self.assertIn('AIChatbot', settings.INSTALLED_APPS)
        self.assertIn('KCLTicketingSystems', settings.INSTALLED_APPS)

    def test_templates_config(self):
        self.assertTrue(settings.TEMPLATES)
        self.assertIn('BACKEND', settings.TEMPLATES[0])

    def test_wsgi_application(self):
        self.assertEqual(settings.WSGI_APPLICATION, 'KCLTicketingSystem.wsgi.application')
