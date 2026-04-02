from rest_framework.permissions import BasePermission


class IsInternalService(BasePermission):
    def has_permission(self, request, view):
        token = request.auth
        if not token:
            return False
        return token.get("role") == "internal_service"

class IsSeller(BasePermission):
    """Allows access only to users with the Seller role."""
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.role == "seller"
        )


class IsAdminUserRole(BasePermission):
    def has_permission(self, request, view):
        token = request.auth
        if not token:
            return False
        return token.get("role") == "admin"