"""
DRF permission classes — a thin translation of `roles.py` into something views
can declare. No role strings live here; this file only asks `user_can(...)`.

    permission_classes = [CanBook]

Views whose rule depends on the *object* rather than the role (only the provider
on this booking may estimate it) keep their explicit party checks — see the note
in roles.py.
"""

from rest_framework.permissions import BasePermission

from .roles import Capability, user_can


def requires(capability, message):
    """Build a permission class for one capability.

    A factory rather than six near-identical class bodies: the interesting part
    of each is a single constant, and this keeps that obvious.
    """

    class _HasCapability(BasePermission):
        def has_permission(self, request, view):
            return user_can(request.user, capability)

    _HasCapability.required_capability = capability
    _HasCapability.message = message
    _HasCapability.__name__ = f"Requires_{capability}"
    return _HasCapability


# Customer side
CanBook = requires(Capability.BOOK, "Only customers can create bookings.")
CanPay = requires(Capability.PAY, "Only customers can pay for a booking.")
CanReview = requires(Capability.REVIEW, "Only customers can leave a review.")

# Provider side
CanOnboard = requires(Capability.ONBOARD, "Only providers can onboard.")
CanManageProfile = requires(
    Capability.MANAGE_PROFILE, "Only providers have a provider profile.",
)
CanManageOfferings = requires(
    Capability.MANAGE_OFFERINGS, "Only providers can manage offerings.",
)
CanViewPriceHistory = requires(
    Capability.VIEW_PRICE_HISTORY, "Only providers can view price history.",
)
