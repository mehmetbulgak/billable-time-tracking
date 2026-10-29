from typing import Any, cast

from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.accounts.sessions import lock_session, start_session


class AccessSessionSerializer(serializers.Serializer):
    access = serializers.CharField(read_only=True)
    csrf_token = serializers.CharField(read_only=True)


class CSRFTokenSerializer(serializers.Serializer):
    csrf_token = serializers.CharField(read_only=True)


class LoginSerializer(TokenObtainPairSerializer):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["email"] = serializers.EmailField(max_length=254)
        self.fields["password"] = serializers.CharField(
            max_length=1024, write_only=True, trim_whitespace=False
        )

    @transaction.atomic
    def validate(self, attrs: dict[str, Any]) -> dict[str, str]:
        data = super().validate(attrs)
        if not isinstance(self.user, User):
            raise AuthenticationFailed("Invalid account.")
        token = start_session(self.user, RefreshToken(cast("Any", data["refresh"])))
        return {"access": str(token.access_token), "refresh": str(token)}


class SessionRefreshSerializer(TokenRefreshSerializer):
    @transaction.atomic
    def validate(self, attrs: dict[str, Any]) -> dict[str, str]:
        token = RefreshToken(cast("Any", attrs["refresh"]))
        session = lock_session(token)
        data = super().validate(attrs)
        refreshed = RefreshToken(cast("Any", data["refresh"]))
        refreshed["exp"] = int(session.expires_at.timestamp())
        OutstandingToken.objects.filter(jti=refreshed["jti"]).update(
            token=str(refreshed),
            expires_at=session.expires_at,
        )
        access = refreshed.access_token
        access["exp"] = min(access["exp"], refreshed["exp"])
        return {"access": str(access), "refresh": str(refreshed)}
