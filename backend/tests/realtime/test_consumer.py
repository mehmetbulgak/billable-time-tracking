from collections.abc import AsyncIterator

import pytest
from asgiref.sync import sync_to_async
from channels.routing import URLRouter
from channels.security.websocket import OriginValidator
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.accounts.sessions import start_session
from apps.realtime.middleware import JWTSubprotocolAuthMiddleware
from apps.realtime.publisher import publish_organization_event
from apps.realtime.routing import websocket_urlpatterns
from tests.factories import UserFactory
from tests.websocket import ActivitySocket

pytestmark = pytest.mark.django_db(transaction=True)

application = OriginValidator(
    JWTSubprotocolAuthMiddleware(URLRouter(websocket_urlpatterns)),
    ["http://testserver"],
)


def token_for(user: User) -> str:
    return str(start_session(user, RefreshToken.for_user(user)).access_token)


@pytest.fixture
async def member() -> User:
    return await sync_to_async(UserFactory)()


@pytest.fixture
async def connected(member: User) -> AsyncIterator[ActivitySocket]:
    communicator = ActivitySocket(application, token=await sync_to_async(token_for)(member))
    connected, _ = await communicator.connect()
    assert connected
    yield communicator
    await communicator.disconnect()


async def test_rejects_connections_without_a_token() -> None:
    communicator = ActivitySocket(application, "/ws/activity/")

    connected, _ = await communicator.connect()

    assert connected is False


async def test_rejects_invalid_tokens() -> None:
    communicator = ActivitySocket(application, token="not-a-jwt")

    connected, _ = await communicator.connect()

    assert connected is False


async def test_receives_events_of_its_organization(
    connected: ActivitySocket,
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
    connected: ActivitySocket,
) -> None:
    outsider = await sync_to_async(UserFactory)()

    await sync_to_async(publish_organization_event)(outsider.organization_id, "timer.started", {})

    assert await connected.receive_nothing(timeout=0.2)


async def test_answers_pings(connected: ActivitySocket) -> None:
    await connected.send_json_to({"type": "ping"})

    assert await connected.receive_json_from() == {"event": "pong", "payload": {}}


@pytest.mark.parametrize(
    "origin", [None, "https://attacker.example", "http://testserver.attacker.example"]
)
async def test_origin_must_match_the_allowed_site(member: User, origin: str | None) -> None:
    socket = ActivitySocket(
        application, token=await sync_to_async(token_for)(member), origin=origin
    )
    accepted, _ = await socket.connect()
    assert not accepted
    await socket.disconnect()


async def test_query_string_tokens_are_not_accepted(member: User) -> None:
    token = await sync_to_async(token_for)(member)
    socket = ActivitySocket(application, f"/ws/activity/?token={token}")
    accepted, _ = await socket.connect()
    assert not accepted
    await socket.disconnect()


async def test_members_cannot_receive_invoice_events(
    connected: ActivitySocket, member: User
) -> None:
    await sync_to_async(publish_organization_event)(
        member.organization_id,
        "invoice.changed",
        {
            "invoice_id": 9,
            "status": "paid",
        },
    )
    assert await connected.receive_nothing(timeout=0.1)


@pytest.mark.parametrize("event", ["entry.changed", "entry.deleted"])
async def test_colleague_history_is_not_sent_to_members(
    connected: ActivitySocket,
    member: User,
    event: str,
) -> None:
    payload = {
        "user_id": member.pk + 1,
        "entry_id": 12,
        "entry": {
            "id": 12,
            "user": {"id": member.pk + 1},
            "description": "private history",
        },
    }
    await sync_to_async(publish_organization_event)(member.organization_id, event, payload)
    assert await connected.receive_json_from() == {"event": "activity.changed", "payload": {}}


async def test_deactivated_users_lose_their_connection(
    connected: ActivitySocket, member: User
) -> None:
    await sync_to_async(User.objects.filter(pk=member.pk).update)(is_active=False)
    await connected.send_json_to({"type": "ping"})
    assert await connected.receive_json_from() == {"event": "session.revoked", "payload": {}}
    assert await connected.receive_output() == {"type": "websocket.close", "code": 4401}


async def test_oversized_websocket_messages_are_rejected(connected: ActivitySocket) -> None:
    await connected.send_input({"type": "websocket.receive", "text": "x" * 4097})
    assert await connected.receive_output() == {"type": "websocket.close", "code": 1009}


async def test_token_expiry_closes_idle_connections(member: User) -> None:
    import time

    def short_token() -> str:
        token = start_session(member, RefreshToken.for_user(member)).access_token
        token["exp"] = int(time.time()) + 1
        return str(token)

    socket = ActivitySocket(application, token=await sync_to_async(short_token)())
    accepted, _ = await socket.connect()
    assert accepted
    result = await socket.receive_output(timeout=2)
    assert result == {"type": "websocket.close", "code": 4401}
    await socket.disconnect()


async def test_logout_closes_an_idle_connection(member: User) -> None:
    from apps.accounts.sessions import revoke_session

    refresh = await sync_to_async(lambda: start_session(member, RefreshToken.for_user(member)))()
    socket = ActivitySocket(application, token=str(refresh.access_token))
    accepted, _ = await socket.connect()
    assert accepted
    await sync_to_async(revoke_session)(str(refresh))
    assert await socket.receive_json_from() == {"event": "session.revoked", "payload": {}}
    assert await socket.receive_output() == {"type": "websocket.close", "code": 4401}
    await socket.disconnect()
