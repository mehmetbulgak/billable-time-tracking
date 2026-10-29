from contextlib import suppress
from datetime import UTC, datetime
from typing import Any, cast

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.middleware.csrf import get_token, rotate_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.session_serializers import (
    AccessSessionSerializer,
    CSRFTokenSerializer,
    LoginSerializer,
    SessionRefreshSerializer,
)
from apps.accounts.sessions import revoke_session
from apps.accounts.throttles import AccountLoginRateThrottle, LoginRateThrottle, RefreshRateThrottle


def _session_response(request: Request, data: dict[str, str]) -> Response:
    token = RefreshToken(cast("Any", data["refresh"]))
    response = Response({"access": data["access"], "csrf_token": get_token(request)})
    response.set_cookie(
        settings.REFRESH_COOKIE_NAME,
        data["refresh"],
        expires=datetime.fromtimestamp(token["exp"], tz=UTC),
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite="Strict",
        path=settings.REFRESH_COOKIE_PATH,
    )
    response["Cache-Control"] = "no-store"
    return response


class CSRFTokenView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = (RefreshRateThrottle,)

    @extend_schema(responses=CSRFTokenSerializer)
    def get(self, request: Request) -> Response:
        response = Response({"csrf_token": get_token(request)})
        response["Cache-Control"] = "no-store"
        return response


@method_decorator(csrf_protect, name="dispatch")
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    throttle_classes = (LoginRateThrottle, AccountLoginRateThrottle)

    @extend_schema(request=LoginSerializer, responses=AccessSessionSerializer)
    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rotate_token(request)
        return _session_response(request, serializer.validated_data)


@method_decorator(csrf_protect, name="dispatch")
class RefreshView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = (RefreshRateThrottle,)

    @extend_schema(request=None, responses=AccessSessionSerializer)
    def post(self, request: Request) -> Response:
        raw_token = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
        serializer = SessionRefreshSerializer(data={"refresh": raw_token or ""})
        try:
            if not raw_token:
                raise AuthenticationFailed("No active session.")
            serializer.is_valid(raise_exception=True)
        except (TokenError, AuthenticationFailed, ObjectDoesNotExist):
            response = Response({"detail": "This session is no longer active."}, status=401)
            response.delete_cookie(
                settings.REFRESH_COOKIE_NAME, path=settings.REFRESH_COOKIE_PATH, samesite="Strict"
            )
            response["Cache-Control"] = "no-store"
            return response
        return _session_response(request, serializer.validated_data)


@method_decorator(csrf_protect, name="dispatch")
class LogoutView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = (RefreshRateThrottle,)

    @extend_schema(request=None, responses={204: None})
    def post(self, request: Request) -> Response:
        raw_token = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
        if raw_token:
            with suppress(TokenError, AuthenticationFailed, ObjectDoesNotExist):
                revoke_session(raw_token)
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(
            settings.REFRESH_COOKIE_NAME, path=settings.REFRESH_COOKIE_PATH, samesite="Strict"
        )
        response["Cache-Control"] = "no-store"
        return response
