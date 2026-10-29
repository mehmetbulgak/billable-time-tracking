from typing import Any

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import Token

from apps.accounts.authentication import SessionJWTAuthentication
from apps.accounts.models import User

_authentication = SessionJWTAuthentication()


@database_sync_to_async
def authenticate_protocols(protocols: list[str]) -> tuple[User | AnonymousUser, Token | None]:
    tokens = [
        protocol.removeprefix("bearer.") for protocol in protocols if protocol.startswith("bearer.")
    ]
    if "billable.v1" not in protocols or len(tokens) != 1 or len(tokens[0]) > 8192:
        return AnonymousUser(), None
    try:
        token = _authentication.get_validated_token(tokens[0].encode())
        user = _authentication.get_user(token)
    except (InvalidToken, AuthenticationFailed):
        return AnonymousUser(), None
    if not isinstance(user, User):
        return AnonymousUser(), None
    return user, token


class JWTSubprotocolAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> Any:
        user, token = await authenticate_protocols(scope.get("subprotocols", []))
        scope = {**scope, "user": user, "auth_token": token}
        return await super().__call__(scope, receive, send)
