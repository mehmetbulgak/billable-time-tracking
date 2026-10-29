from collections.abc import Callable
from datetime import timedelta
from typing import Any

import pytest
from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import LoginSession, User
from tests.factories import UserFactory

pytestmark = pytest.mark.django_db
PASSWORD = "correct-horse-battery"


def sign_in(api: APIClient, user: User) -> Any:
    csrf = api.get("/api/v1/auth/csrf/")
    api.credentials(HTTP_X_CSRFTOKEN=csrf.data["csrf_token"], HTTP_ORIGIN="http://testserver")
    result = api.post("/api/v1/auth/token/", {"email": user.email, "password": PASSWORD})
    assert result.status_code == 200
    api.credentials(HTTP_X_CSRFTOKEN=result.data["csrf_token"], HTTP_ORIGIN="http://testserver")
    return result


@pytest.mark.parametrize("path", ["token/", "token/refresh/", "logout/"])
def test_cookie_authentication_requires_csrf(path: str, member: User) -> None:
    api = APIClient(enforce_csrf_checks=True)
    result = api.post(f"/api/v1/auth/{path}", {"email": member.email, "password": PASSWORD})
    assert result.status_code == 403


@pytest.mark.parametrize("path", ["token/", "token/refresh/", "logout/"])
def test_foreign_origins_cannot_use_auth_cookies(path: str, member: User) -> None:
    api = APIClient(enforce_csrf_checks=True)
    sign_in(api, member)
    api.credentials(
        HTTP_X_CSRFTOKEN=api.get("/api/v1/auth/csrf/").data["csrf_token"],
        HTTP_ORIGIN="https://attacker.example",
    )
    assert api.post(f"/api/v1/auth/{path}").status_code == 403


@override_settings(SESSION_COOKIE_SECURE=True, CSRF_COOKIE_SECURE=True)
def test_refresh_token_is_only_in_a_protected_cookie(member: User) -> None:
    api = APIClient()
    result = sign_in(api, member)
    cookie = result.cookies[settings.REFRESH_COOKIE_NAME]
    assert set(result.data) == {"access", "csrf_token"}
    assert cookie["httponly"]
    assert cookie["secure"]
    assert cookie["samesite"] == "Strict"
    assert cookie["path"] == "/api/v1/auth/"
    assert not cookie["domain"]
    assert result["Cache-Control"] == "no-store"


def test_csrf_protected_login_refresh_and_logout_work(member: User) -> None:
    api = APIClient(enforce_csrf_checks=True)
    result = sign_in(api, member)
    assert api.post("/api/v1/auth/token/refresh/").status_code == 200
    assert api.post("/api/v1/auth/logout/").status_code == 204
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {result.data['access']}")
    assert api.get("/api/v1/auth/me/").status_code == 401


def test_rotated_refresh_cannot_be_replayed(member: User) -> None:
    api = APIClient()
    sign_in(api, member)
    original = api.cookies[settings.REFRESH_COOKIE_NAME].value
    assert api.post("/api/v1/auth/token/refresh/").status_code == 200
    assert BlacklistedToken.objects.count() == 1
    api.cookies[settings.REFRESH_COOKIE_NAME] = original
    assert api.post("/api/v1/auth/token/refresh/").status_code == 401


def test_logout_with_previous_refresh_revokes_the_whole_session(member: User) -> None:
    api = APIClient()
    initial = sign_in(api, member)
    original = api.cookies[settings.REFRESH_COOKIE_NAME].value
    refreshed = api.post("/api/v1/auth/token/refresh/")
    rotated = api.cookies[settings.REFRESH_COOKIE_NAME].value
    api.cookies[settings.REFRESH_COOKIE_NAME] = original
    assert api.post("/api/v1/auth/logout/").status_code == 204
    for token in (initial.data["access"], refreshed.data["access"]):
        api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        assert api.get("/api/v1/auth/me/").status_code == 401
    api.cookies[settings.REFRESH_COOKIE_NAME] = rotated
    assert api.post("/api/v1/auth/token/refresh/").status_code == 401


def test_separate_visitors_have_independent_sessions(member: User) -> None:
    first, second = APIClient(), APIClient()
    sign_in(first, member)
    second_tokens = sign_in(second, member)
    first.post("/api/v1/auth/logout/")
    second.credentials(HTTP_AUTHORIZATION=f"Bearer {second_tokens.data['access']}")
    assert second.get("/api/v1/auth/me/").status_code == 200
    assert second.post("/api/v1/auth/token/refresh/").status_code == 200


@pytest.mark.parametrize("change", ["deactivate", "password", "expire", "delete"])
def test_account_changes_immediately_invalidate_access_and_refresh(
    member: User, change: str
) -> None:
    api = APIClient()
    result = sign_in(api, member)
    if change == "deactivate":
        User.objects.filter(pk=member.pk).update(is_active=False)
    elif change == "password":
        member.set_password("different-strong-password")
        member.save(update_fields=("password",))
    elif change == "expire":
        LoginSession.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
    else:
        member.delete()
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {result.data['access']}")
    assert api.get("/api/v1/auth/me/").status_code == 401
    assert api.post("/api/v1/auth/token/refresh/").status_code == 401


def test_refresh_requires_the_cookie_not_a_json_token(member: User) -> None:
    api = APIClient()
    sign_in(api, member)
    refresh = api.cookies[settings.REFRESH_COOKIE_NAME].value
    api.cookies.clear()
    assert api.post("/api/v1/auth/token/refresh/", {"refresh": refresh}).status_code == 401


def test_access_without_a_server_session_is_rejected(member: User) -> None:
    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(member)}")
    assert api.get("/api/v1/auth/me/").status_code == 401


def test_login_is_case_insensitive_and_emails_are_unique(member: User) -> None:
    api = APIClient()
    assert (
        api.post(
            "/api/v1/auth/token/",
            {
                "email": member.email.upper(),
                "password": PASSWORD,
            },
        ).status_code
        == 200
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        UserFactory(email=member.email.upper())


@override_settings(DEMO_MODE=True)
@pytest.mark.parametrize(
    ("path", "payload"),
    [
        ("/api/v1/auth/me/", {"first_name": "attacker"}),
        ("/api/v1/organization/", {"name": "attacker"}),
    ],
)
def test_demo_account_and_organization_changes_are_denied(
    client_for: Callable[[User], APIClient],
    manager: User,
    path: str,
    payload: dict[str, str],
) -> None:
    assert client_for(manager).patch(path, payload).status_code == 403


@override_settings(DEMO_MODE=True)
def test_demo_member_changes_are_denied(
    client_for: Callable[[User], APIClient], manager: User, member: User
) -> None:
    api = client_for(manager)
    assert api.patch(f"/api/v1/members/{member.pk}/", {"is_active": False}).status_code == 403
    assert api.post("/api/v1/members/", {"email": "new@example.test"}).status_code == 403
    member.refresh_from_db()
    assert member.is_active


@override_settings(AUTH_THROTTLING_ENABLED=True)
def test_login_throttle_limits_invalid_attempts_from_one_address(member: User) -> None:
    cache.clear()
    api = APIClient()
    for _ in range(10):
        assert (
            api.post(
                "/api/v1/auth/token/",
                {
                    "email": member.email,
                    "password": "incorrect",
                },
            ).status_code
            == 401
        )
    assert (
        api.post(
            "/api/v1/auth/token/",
            {
                "email": member.email,
                "password": PASSWORD,
            },
        ).status_code
        == 429
    )
    cache.clear()
