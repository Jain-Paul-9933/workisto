"""Unit tests for the token boundary — no DB, no network."""

import time

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from search_service import config
from search_service.auth import verify_token


def _creds(token):
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def _token(secret=config.JWT_SECRET, **overrides):
    payload = {"sub": "1", "role": "CUSTOMER", "exp": int(time.time()) + 60}
    payload.update(overrides)
    return jwt.encode(payload, secret, algorithm=config.JWT_ALGORITHM)


def test_valid_token_is_accepted():
    claims = verify_token(_creds(_token()))
    assert claims["sub"] == "1"


def test_expired_token_is_rejected():
    with pytest.raises(HTTPException) as exc:
        verify_token(_creds(_token(exp=int(time.time()) - 1)))
    assert exc.value.status_code == 401


def test_wrong_signature_is_rejected():
    with pytest.raises(HTTPException) as exc:
        verify_token(_creds(_token(secret="not-the-shared-secret")))
    assert exc.value.status_code == 401
