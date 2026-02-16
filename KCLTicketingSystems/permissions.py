from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Custom permission to only allow admin users to access the view.
    Checks if user is admin role, staff, or superuser.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (
                (hasattr(request.user, 'role') and request.user.role == 'admin') or
                request.user.is_superuser or
                request.user.is_staff
            )
        )
