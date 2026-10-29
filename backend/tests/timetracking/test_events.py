from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any

import pytest
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.realtime.publisher import organization_group
from tests.factories import ProjectFactory

CaptureCallbacks = Callable[..., AbstractContextManager[list[Callable[[], object]]]]


@pytest.fixture
def listener(organization: Organization) -> Callable[[], dict[str, Any]]:
    layer = get_channel_layer()
    channel = async_to_sync(layer.new_channel)()
    async_to_sync(layer.group_add)(organization_group(organization.pk), channel)

    def receive() -> dict[str, Any]:
        message: dict[str, Any] = async_to_sync(layer.receive)(channel)
        return message

    return receive


def test_starting_and_stopping_a_timer_is_broadcast(
    client_for: Callable[[User], APIClient],
    member: User,
    organization: Organization,
    listener: Callable[[], dict[str, Any]],
    django_capture_on_commit_callbacks: CaptureCallbacks,
) -> None:
    project = ProjectFactory(client__organization=organization)
    api = client_for(member)

    with django_capture_on_commit_callbacks(execute=True):
        api.post("/api/v1/time-entries/start/", {"project": project.pk})
    started = listener()
    with django_capture_on_commit_callbacks(execute=True):
        api.post("/api/v1/time-entries/stop/")
    stopped = listener()

    assert started["event"] == "timer.started"
    assert started["payload"]["entry"]["user"]["id"] == member.pk
    assert started["payload"]["entry"]["project"]["id"] == project.pk
    assert stopped["event"] == "timer.stopped"
    assert stopped["payload"]["entry"]["is_running"] is False


def test_events_are_not_sent_when_the_transaction_fails(
    client_for: Callable[[User], APIClient],
    member: User,
    django_capture_on_commit_callbacks: CaptureCallbacks,
) -> None:
    with django_capture_on_commit_callbacks() as callbacks:
        response = client_for(member).post("/api/v1/time-entries/stop/")

    assert response.status_code == 404
    assert callbacks == []
