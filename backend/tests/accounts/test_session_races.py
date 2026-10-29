from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.conf import settings
from django.db import close_old_connections
from rest_framework.test import APIClient

from apps.accounts.models import User
from tests.factories import UserFactory

pytestmark = pytest.mark.django_db(transaction=True)


def run_requests(paths: list[str], cookie: str) -> list[int]:
    barrier = Barrier(len(paths))

    def request(path: str) -> int:
        close_old_connections()
        try:
            api = APIClient()
            api.cookies[settings.REFRESH_COOKIE_NAME] = cookie
            barrier.wait(timeout=5)
            return int(api.post(path).status_code)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=len(paths)) as executor:
        return list(executor.map(request, paths))


def login() -> tuple[User, APIClient, str]:
    user = UserFactory()
    api = APIClient()
    result = api.post(
        "/api/v1/auth/token/",
        {
            "email": user.email,
            "password": "correct-horse-battery",
        },
    )
    assert result.status_code == 200
    return user, api, api.cookies[settings.REFRESH_COOKIE_NAME].value


def test_concurrent_refreshes_cannot_reuse_the_same_token() -> None:
    _, _, cookie = login()
    statuses = run_requests(["/api/v1/auth/token/refresh/"] * 2, cookie)
    assert sorted(statuses) == [200, 401]


def test_concurrent_refresh_cannot_resurrect_a_logged_out_session() -> None:
    user, api, cookie = login()
    statuses = run_requests(["/api/v1/auth/token/refresh/", "/api/v1/auth/logout/"], cookie)
    assert statuses[0] in {200, 401}
    assert statuses[1] == 204
    assert user.login_sessions.get().revoked_at is not None
    assert api.post("/api/v1/auth/token/refresh/").status_code == 401
