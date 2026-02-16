from rest_framework.permissions import BasePermission
from functools import wraps
from django.http import JsonResponse


class IsAdmin(BasePermission):
    """
    Custom permission to only allow admin users to access the view.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'role') and
            request.user.role == 'admin'
        )


def admin_required(view_func):
    """
    Decorator for function-based views to ensure user is admin.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {'error': 'Authentication required'},
                status=401
            )
        
        if not hasattr(request.user, 'role') or request.user.role != 'admin':
            return JsonResponse(
                {'error': 'Admin access required'},
                status=403
            )
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
