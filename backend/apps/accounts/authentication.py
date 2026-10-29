from uuid import UUID

from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import Token

from apps.accounts.models import LoginSession, User


def session_id_for(token: Token) -> UUID:
    try:
        return UUID(str(token["sid"]))
    except (KeyError, ValueError, TypeError) as error:
        raise AuthenticationFailed("Invalid session.", code="invalid_session") from error


class SessionJWTAuthentication(BaseAuthentication):
    jwt = JWTAuthentication()

    def authenticate(self, request: Request) -> tuple[User, Token] | None:
        header = self.jwt.get_header(request)
        if header is None:
            return None
        raw_token = self.jwt.get_raw_token(header)
        if raw_token is None:
            return None
        token = self.get_validated_token(raw_token)
        return self.get_user(token), token

    def authenticate_header(self, request: Request) -> str:
        return self.jwt.authenticate_header(request)

    def get_validated_token(self, raw_token: bytes) -> Token:
        return self.jwt.get_validated_token(raw_token)

    def get_user(self, validated_token: Token) -> User:
        user = self.jwt.get_user(validated_token)
        if (
            not isinstance(user, User)
            or not LoginSession.objects.filter(
                pk=session_id_for(validated_token),
                user=user,
                revoked_at__isnull=True,
                expires_at__gt=timezone.now(),
            ).exists()
        ):
            raise AuthenticationFailed("This session is no longer active.", code="session_revoked")
        return user
