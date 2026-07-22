"""
Role-based permission classes — the auth foundation the provider/booking
endpoints build on. `IsAuthenticated` answers "are you logged in?"; these answer
"are you the right *kind* of user?".
"""

from rest_framework.permissions import BasePermission

from .models import User


class IsProvider(BasePermission):
    message = "Only providers can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.PROVIDER
        )


class IsCustomer(BasePermission):
    message = "Only customers can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.CUSTOMER
        )
