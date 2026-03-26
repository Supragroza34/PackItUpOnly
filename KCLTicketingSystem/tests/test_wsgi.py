import importlib
import sys
from django.test import SimpleTestCase

class WSGIApplicationTest(SimpleTestCase):
    def test_wsgi_application_callable(self):
        # Import the WSGI module and check for 'application' callable
        wsgi_module = importlib.import_module('KCLTicketingSystem.wsgi')
        self.assertTrue(hasattr(wsgi_module, 'application'))
        self.assertTrue(callable(wsgi_module.application))

    def test_wsgi_application_env(self):
        # Ensure DJANGO_SETTINGS_MODULE is set correctly
        import KCLTicketingSystem.wsgi
        self.assertEqual(
            os.environ.get('DJANGO_SETTINGS_MODULE'),
            'KCLTicketingSystem.settings'
        )
