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
