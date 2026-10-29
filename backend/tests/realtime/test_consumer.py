from collections.abc import AsyncIterator

import pytest
from asgiref.sync import sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import User
from apps.realtime.middleware import JWTQueryStringAuthMiddleware
from apps.realtime.publisher import publish_organization_event
from apps.realtime.routing import websocket_urlpatterns
from tests.factories import UserFactory

pytestmark = pytest.mark.django_db(transaction=True)

application = JWTQueryStringAuthMiddleware(URLRouter(websocket_urlpatterns))


def token_for(user: User) -> str:
    return str(AccessToken.for_user(user))


@pytest.fixture
async def member() -> User:
    return await sync_to_async(UserFactory)()


@pytest.fixture
async def connected(member: User) -> AsyncIterator[WebsocketCommunicator]:
    communicator = WebsocketCommunicator(application, f"/ws/activity/?token={token_for(member)}")
    connected, _ = await communicator.connect()
    assert connected
    yield communicator
    await communicator.disconnect()


async def test_rejects_connections_without_a_token() -> None:
    communicator = WebsocketCommunicator(application, "/ws/activity/")

    connected, _ = await communicator.connect()

    assert connected is False


async def test_rejects_invalid_tokens() -> None:
    communicator = WebsocketCommunicator(application, "/ws/activity/?token=not-a-jwt")

    connected, _ = await communicator.connect()

    assert connected is False


async def test_receives_events_of_its_organization(
    connected: WebsocketCommunicator,
    member: User,
) -> None:
    await sync_to_async(publish_organization_event)(
        member.organization_id,
        "timer.started",
        {"entry": {"id": 1}},
    )

    message = await connected.receive_json_from()

    assert message == {"event": "timer.started", "payload": {"entry": {"id": 1}}}


async def test_does_not_receive_events_of_other_organizations(
    connected: WebsocketCommunicator,
) -> None:
    outsider = await sync_to_async(UserFactory)()

    await sync_to_async(publish_organization_event)(outsider.organization_id, "timer.started", {})

    assert await connected.receive_nothing(timeout=0.2)


async def test_answers_pings(connected: WebsocketCommunicator) -> None:
    await connected.send_json_to({"type": "ping"})

    assert await connected.receive_json_from() == {"event": "pong", "payload": {}}
