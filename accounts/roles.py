"""
What each role is allowed to do — the whole authorization model on one screen.

Before this module the rule was scattered: an inline `role != CUSTOMER` check in
a booking view, an `IsProvider` class in another file, and an `IsCustomer` class
nobody used. Reading "who may do what" meant grepping. Now the answer is the
table below, and `permissions.py` only turns it into DRF classes.

Two kinds of check are deliberately kept apart:

  * **Capability** (here) — role-determined and object-independent: "may a
    provider create bookings at all?" A single account has one role, so this is
    answerable from the user alone.
  * **Party** (stays in the views) — "is this *my* booking, and am I the right
    side of it?" e.g. only the provider on booking #7 may estimate it. That
    depends on the row, not the role, so a capability table can't express it and
    shouldn't pretend to.

Adding a capability is a one-line change here plus a permission class alias.
"""

from .models import User


class Capability:
    """Named actions. Strings (not an Enum) so they read plainly in tests."""

    # Customer side
    BOOK = "book"
    PAY = "pay"
    REVIEW = "review"

    # Provider side
    ONBOARD = "onboard"
    MANAGE_PROFILE = "manage_profile"
    MANAGE_OFFERINGS = "manage_offerings"
    VIEW_PRICE_HISTORY = "view_price_history"


# One account has exactly one role, so these sets are disjoint by design: a
# provider cannot book and a customer cannot sell. That is the product rule —
# if it ever changes, it changes *here*, not across six view files.
#
# ADMIN gets nothing: staff work happens in Django admin, which has its own
# permission system. An admin hitting the customer/provider API is a mistake, so
# it fails closed.
ROLE_CAPABILITIES = {
    User.Role.CUSTOMER: frozenset({
        Capability.BOOK,
        Capability.PAY,
        Capability.REVIEW,
    }),
    User.Role.PROVIDER: frozenset({
        Capability.ONBOARD,
        Capability.MANAGE_PROFILE,
        Capability.MANAGE_OFFERINGS,
        Capability.VIEW_PRICE_HISTORY,
    }),
    User.Role.ADMIN: frozenset(),
}


def capabilities_for(role):
    """Every capability a role has. Unknown roles get nothing, not an error —
    an unrecognised role should lock the door, not crash the request."""
    return ROLE_CAPABILITIES.get(role, frozenset())


def user_can(user, capability):
    """The single question the permission classes ask."""
    if not user or not user.is_authenticated:
        return False
    return capability in capabilities_for(user.role)
