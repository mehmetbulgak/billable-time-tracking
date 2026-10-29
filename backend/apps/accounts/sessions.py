from datetime import UTC, datetime
from typing import Any, cast

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken
from rest_framework_simplejwt.utils import get_md5_hash_password

from apps.accounts.authentication import session_id_for
from apps.accounts.models import LoginSession, User


def session_group(session_id: object) -> str:
    return f"session.{session_id}"


def start_session(user: User, token: RefreshToken) -> RefreshToken:
    session = LoginSession.objects.create(
        user=user,
        expires_at=datetime.fromtimestamp(token["exp"], tz=UTC),
    )
    token["sid"] = str(session.pk)
    OutstandingToken.objects.filter(jti=token["jti"]).update(token=str(token))
    return token


def lock_session(token: RefreshToken | UntypedToken) -> LoginSession:
    session = (
        LoginSession.objects.select_for_update(of=("self",))
        .select_related("user")
        .filter(pk=session_id_for(token), user_id=token.get(api_settings.USER_ID_CLAIM))
        .first()
    )
    if (
        session is None
        or session.revoked_at is not None
        or session.expires_at <= timezone.now()
        or not session.user.is_active
        or token.get(api_settings.REVOKE_TOKEN_CLAIM)
        != get_md5_hash_password(session.user.password)
    ):
        raise AuthenticationFailed("This session is no longer active.", code="session_revoked")
    return session


@transaction.atomic
def revoke_session(raw_token: str) -> None:
    token = UntypedToken(cast("Any", raw_token))
    if token.get("token_type") != "refresh":
        raise AuthenticationFailed("Invalid refresh token.")
    session = lock_session(token)
    session.revoked_at = timezone.now()
    session.save(update_fields=("revoked_at",))
    layer = get_channel_layer()
    if layer is not None:
        transaction.on_commit(
            lambda: async_to_sync(layer.group_send)(
                session_group(session.pk),
                {"type": "session.revoked"},
            ),
            robust=True,
        )
