"""Serve the React SPA index for the main site and client-side routes."""

from django.http import HttpResponse
from django.conf import settings

# Path to React build index (when frontend is built for production)
FRONTEND_INDEX = settings.BASE_DIR / 'frontend' / 'build' / 'index.html'


def home(request):
    """Serve React app index so SPA starts at sign-in."""
    if FRONTEND_INDEX.exists():
        with open(FRONTEND_INDEX, encoding='utf-8') as f:
            return HttpResponse(f.read(), content_type='text/html')
    return HttpResponse("Frontend build not found.", status=503)


def spa_catchall(request, path):
    """Serve the same index.html for all SPA routes (e.g. /login, /dashboard)."""
    if FRONTEND_INDEX.exists():
        with open(FRONTEND_INDEX, encoding='utf-8') as f:
            return HttpResponse(f.read(), content_type='text/html')
    return HttpResponse("Frontend build not found.", status=503)