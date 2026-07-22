import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api():
    return APIClient()


@pytest.mark.django_db
def test_register_defaults_to_customer(api):
    resp = api.post(
        "/api/auth/register/",
        {"email": "cust@example.com", "password": "s3cret-pass-123"},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.data["role"] == "CUSTOMER"
    # The password must never come back out.
    assert "password" not in resp.data
    assert User.objects.filter(email="cust@example.com").exists()


@pytest.mark.django_db
def test_register_as_provider(api):
    resp = api.post(
        "/api/auth/register/",
        {"email": "pro@example.com", "password": "s3cret-pass-123", "role": "PROVIDER"},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.data["role"] == "PROVIDER"


@pytest.mark.django_db
def test_cannot_self_register_as_admin(api):
    resp = api.post(
        "/api/auth/register/",
        {"email": "sneaky@example.com", "password": "s3cret-pass-123", "role": "ADMIN"},
        format="json",
    )
    # ADMIN isn't an allowed choice → validation error, no user created.
    assert resp.status_code == 400
    assert not User.objects.filter(email="sneaky@example.com").exists()


@pytest.mark.django_db
def test_weak_password_rejected(api):
    resp = api.post(
        "/api/auth/register/",
        {"email": "weak@example.com", "password": "123"},
        format="json",
    )
    assert resp.status_code == 400
    assert not User.objects.filter(email="weak@example.com").exists()


@pytest.mark.django_db
def test_login_me_logout_flow(api):
    User.objects.create_user(
        email="u@example.com", password="s3cret-pass-123", role=User.Role.PROVIDER,
    )
    # Anonymous: /me/ is closed (403 — SessionAuth gives no auth challenge).
    assert api.get("/api/me/").status_code == 403

    login = api.post(
        "/api/auth/login/",
        {"email": "u@example.com", "password": "s3cret-pass-123"},
        format="json",
    )
    assert login.status_code == 200

    # The session cookie now rides on the client; /me/ reflects the user.
    me = api.get("/api/me/")
    assert me.status_code == 200
    assert me.data["email"] == "u@example.com"
    assert me.data["role"] == "PROVIDER"

    assert api.post("/api/auth/logout/").status_code == 204
    assert api.get("/api/me/").status_code == 403


@pytest.mark.django_db
def test_login_wrong_password_is_rejected(api):
    User.objects.create_user(email="u@example.com", password="s3cret-pass-123")
    resp = api.post(
        "/api/auth/login/",
        {"email": "u@example.com", "password": "wrong-password"},
        format="json",
    )
    assert resp.status_code == 400
