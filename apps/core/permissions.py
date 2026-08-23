from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """Check that the requesting user owns the object (via user_id or author_id)."""

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user_id'):
            return obj.user_id == request.user.id
        return obj.author_id == request.user.id if hasattr(obj, 'author_id') else False


class IsAdmin(BasePermission):
    """Check that the requesting user has admin role."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsAdminOrAssistant(BasePermission):
    """Check that the requesting user has admin or admin_assistant role."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('admin', 'admin_assistant')
        )


class IsAdminOnly(BasePermission):
    """Restrict access to admin role only (not admin_assistant)."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsAdminOrAssistantReadOnly(BasePermission):
    """
    Admin has full access.
    Admin assistant has read-only access (GET/HEAD/OPTIONS only).
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = request.user.role
        if role == 'admin':
            return True
        if role == 'admin_assistant':
            return request.method in ('GET', 'HEAD', 'OPTIONS')
        return False


class IsAdminOrAssistantNoCreateDelete(BasePermission):
    """
    Admin has full access.
    Admin assistant can read and edit (GET, HEAD, OPTIONS, PUT, PATCH)
    but cannot create (POST) or delete (DELETE).
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = request.user.role
        if role == 'admin':
            return True
        if role == 'admin_assistant':
            return request.method not in ('POST', 'DELETE')
        return False
