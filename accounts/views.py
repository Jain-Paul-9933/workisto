"""
Auth endpoints — session based (see docs/adr/0001-auth.md).

`login()`/`logout()` are Django's own session helpers: login() writes the
session (Redis + DB via the cached_db backend) and sets the httpOnly cookie;
logout() flushes it. That gives us instant, server-side revocation for free.
"""

import time

import jwt
from django.conf import settings
from django.contrib.auth import login, logout
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer


class RegisterView(APIView):
    # DRF's default is IsAuthenticated; signup must override it.
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Sign-up flows straight into a logged-in session (single backend, so
        # login() needs no explicit backend argument).
        login(request, user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        login(request, serializer.validated_data["user"])
        return Response(UserSerializer(serializer.validated_data["user"]).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class SearchTokenView(APIView):
    """GET /api/auth/search-token/ — a short-lived bearer token for the FastAPI
    search service. The service verifies it statelessly with the shared secret;
    we never share Django sessions across that boundary (ADR 0001). The short TTL
    is what lets us skip a revocation list.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = int(time.time())
        token = jwt.encode(
            {
                "sub": str(request.user.id),
                "role": request.user.role,
                "iat": now,
                "exp": now + settings.SEARCH_JWT_TTL_SECONDS,
            },
            settings.SEARCH_JWT_SECRET,
            algorithm="HS256",
        )
        return Response({"token": token, "expires_in": settings.SEARCH_JWT_TTL_SECONDS})
