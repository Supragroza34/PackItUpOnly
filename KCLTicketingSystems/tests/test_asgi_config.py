import importlib
import os
import sys
from unittest import TestCase
from unittest.mock import patch, sentinel


class ASGIConfigTest(TestCase):
    """Group asgi config checks so the user workflow is guarded against regressions."""
    def _reload_asgi_module(self):
        """Support the asgi config tests by reload asgi module so assertions remain focused on outcomes."""
        module_name = "KCLTicketingSystem.asgi"
        if module_name in sys.modules:
            del sys.modules[module_name]
        return importlib.import_module(module_name)

    @patch("django.core.asgi.get_asgi_application", return_value=sentinel.asgi_app)
    def test_asgi_sets_default_settings_module_and_builds_application(self, mock_get_asgi):
        """Guard asgi sets default settings module and builds application in the asgi config flow so regressions surface early."""
        original = os.environ.pop("DJANGO_SETTINGS_MODULE", None)
        try:
            module = self._reload_asgi_module()
            self.assertEqual(
                os.environ.get("DJANGO_SETTINGS_MODULE"),
                "KCLTicketingSystem.settings",
            )
            self.assertIs(module.application, sentinel.asgi_app)
            mock_get_asgi.assert_called_once()
        finally:
            if original is None:
                os.environ.pop("DJANGO_SETTINGS_MODULE", None)
            else:
                os.environ["DJANGO_SETTINGS_MODULE"] = original

    @patch("django.core.asgi.get_asgi_application", return_value=sentinel.asgi_app)
    def test_asgi_does_not_override_existing_settings_module(self, mock_get_asgi):
        """Guard asgi does not override existing settings module in the asgi config flow so regressions surface early."""
        original = os.environ.get("DJANGO_SETTINGS_MODULE")
        os.environ["DJANGO_SETTINGS_MODULE"] = "custom.settings"
        try:
            module = self._reload_asgi_module()
            self.assertEqual(os.environ.get("DJANGO_SETTINGS_MODULE"), "custom.settings")
            self.assertIs(module.application, sentinel.asgi_app)
            mock_get_asgi.assert_called_once()
        finally:
            if original is None:
                os.environ.pop("DJANGO_SETTINGS_MODULE", None)
            else:
                os.environ["DJANGO_SETTINGS_MODULE"] = original
