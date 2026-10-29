from django.conf import settings
from django.utils.crypto import salted_hmac
from rest_framework.request import Request
from rest_framework.settings import api_settings
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView


class LoginRateThrottle(SimpleRateThrottle):
    scope = "login"

    def get_rate(self) -> str | None:
        rate = api_settings.DEFAULT_THROTTLE_RATES[self.scope]
        return str(rate) if rate is not None else None

    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        if not settings.AUTH_THROTTLING_ENABLED:
            return None
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class AccountLoginRateThrottle(LoginRateThrottle):
    scope = "login_account"

    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        if settings.DEMO_MODE or not settings.AUTH_THROTTLING_ENABLED:
            return None
        if not isinstance(request.data, dict):
            return None
        email = request.data.get("email")
        if not isinstance(email, str):
            return None
        identifier = salted_hmac(
            "login-throttle", email.strip().casefold(), algorithm="sha256"
        ).hexdigest()
        return self.cache_format % {"scope": self.scope, "ident": identifier}


class RefreshRateThrottle(LoginRateThrottle):
    scope = "refresh"
