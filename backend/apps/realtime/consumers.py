from typing import Any

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.accounts.models import User
from apps.realtime.publisher import organization_group


class OrganizationActivityConsumer(AsyncJsonWebsocketConsumer):
    group_name: str | None = None

    async def connect(self) -> None:
        user = self.scope.get("user")
        if not isinstance(user, User) or user.organization_id is None:
            await self.close()
            return
        self.group_name = organization_group(user.organization_id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code: int) -> None:
        if self.group_name is not None:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content: Any, **kwargs: Any) -> None:
        if isinstance(content, dict) and content.get("type") == "ping":
            await self.send_json({"event": "pong", "payload": {}})

    async def organization_event(self, message: dict[str, Any]) -> None:
        await self.send_json({"event": message["event"], "payload": message["payload"]})
