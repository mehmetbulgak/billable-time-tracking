from typing import Any
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

from apps.accounts.models import User

_authentication = JWTAuthentication()


def _token_from_query_string(query_string: bytes) -> str | None:
    values = parse_qs(query_string.decode()).get("token")
    return values[0] if values else None


@database_sync_to_async
def _user_for_token(token: str | None) -> User | AnonymousUser:
    if not token:
        return AnonymousUser()
    try:
        validated_token = _authentication.get_validated_token(token.encode())
        user = _authentication.get_user(validated_token)
    except (InvalidToken, AuthenticationFailed):
        return AnonymousUser()
    if isinstance(user, User) and user.is_active:
        return user
    return AnonymousUser()


class JWTQueryStringAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> Any:
        token = _token_from_query_string(scope.get("query_string", b""))
        scope = {**scope, "user": await _user_for_token(token)}
        return await super().__call__(scope, receive, send)
