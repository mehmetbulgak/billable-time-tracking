import json
from collections.abc import Callable, Mapping
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from rest_framework.renderers import JSONRenderer

EVENT_MESSAGE_TYPE = "organization.event"


def organization_group(organization_id: int) -> str:
    return f"organization.{organization_id}"


def _to_primitive(payload: Mapping[str, Any]) -> dict[str, Any]:
    primitive: dict[str, Any] = json.loads(JSONRenderer().render(payload))
    return primitive


def publish_organization_event(
    organization_id: int,
    event: str,
    payload: Mapping[str, Any],
) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        organization_group(organization_id),
        {"type": EVENT_MESSAGE_TYPE, "event": event, "payload": _to_primitive(payload)},
    )


def publish_on_commit(
    organization_id: int,
    event: str,
    payload_factory: Callable[[], Mapping[str, Any]],
) -> None:
    transaction.on_commit(
        lambda: publish_organization_event(organization_id, event, payload_factory()),
        robust=True,
    )
