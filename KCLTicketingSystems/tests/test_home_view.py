"""Tests for Home View."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import TestCase

from KCLTicketingSystems.views import home_view


class HomeViewTests(TestCase):
    def test_home_falls_back_to_template_when_frontend_build_missing(self):
        missing_index = Path("C:/nonexistent/frontend/build/index.html")
        with patch.object(home_view, "FRONTEND_INDEX", missing_index):
            response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "KCL Ticketing System")
        self.assertContains(response, "Go to Login")

    def test_spa_catchall_falls_back_to_template_when_frontend_build_missing(self):
        missing_index = Path("C:/nonexistent/frontend/build/index.html")
        with patch.object(home_view, "FRONTEND_INDEX", missing_index):
            response = self.client.get("/dashboard")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "KCL Ticketing System")

    def test_home_serves_react_index_when_frontend_build_exists(self):
        with TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "index.html"
            index_path.write_text("<html><body><div id='root'>React App</div></body></html>", encoding="utf-8")

            with patch.object(home_view, "FRONTEND_INDEX", index_path):
                response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "React App")
        self.assertEqual(response["Content-Type"], "text/html")

    def test_spa_catchall_serves_react_index_when_frontend_build_exists(self):
        with TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "index.html"
            index_path.write_text("<html><body><div>SPA Route</div></body></html>", encoding="utf-8")

            with patch.object(home_view, "FRONTEND_INDEX", index_path):
                response = self.client.get("/login")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SPA Route")
        self.assertEqual(response["Content-Type"], "text/html")
