"""
The capability table is now the authorization model, so it gets tested directly
rather than only through the endpoints that consume it.
"""

import pytest

from accounts.models import User
from accounts.roles import Capability, capabilities_for, user_can


def test_roles_are_disjoint():
    """One account, one role — a provider must not be able to book, and a
    customer must not be able to sell. If this ever fails, it's a product
    decision, not a typo."""
    customer = capabilities_for(User.Role.CUSTOMER)
    provider = capabilities_for(User.Role.PROVIDER)
    assert customer & provider == frozenset()


def test_admin_has_no_api_capabilities():
    """Staff work happens in Django admin, which has its own permissions."""
    assert capabilities_for(User.Role.ADMIN) == frozenset()


def test_unknown_role_fails_closed():
    """An unrecognised role should lock the door, not raise."""
    assert capabilities_for("SOMETHING_ELSE") == frozenset()


@pytest.mark.django_db
def test_user_can_matches_role():
    customer = User.objects.create_user(
        email="c@example.com", password="x", role=User.Role.CUSTOMER,
    )
    provider = User.objects.create_user(
        email="p@example.com", password="x", role=User.Role.PROVIDER,
    )

    assert user_can(customer, Capability.BOOK)
    assert not user_can(customer, Capability.MANAGE_OFFERINGS)

    assert user_can(provider, Capability.MANAGE_OFFERINGS)
    assert not user_can(provider, Capability.BOOK)


def test_anonymous_can_do_nothing():
    class Anon:
        is_authenticated = False
        role = User.Role.CUSTOMER  # even with a role attribute, it must not count

    assert not user_can(Anon(), Capability.BOOK)
    assert not user_can(None, Capability.BOOK)
