import asyncio
import time
from contextlib import suppress
from typing import Any

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import Token

from apps.accounts.authentication import SessionJWTAuthentication, session_id_for
from apps.accounts.models import User
from apps.accounts.sessions import session_group
from apps.realtime.publisher import organization_group


class OrganizationActivityConsumer(AsyncJsonWebsocketConsumer):
    group_name: str | None = None
    login_group: str | None = None
    expiry_task: asyncio.Task[None] | None = None
    last_ping: float = 0

    async def connect(self) -> None:
        user, token = self.scope.get("user"), self.scope.get("auth_token")
        if (
            not isinstance(user, User)
            or user.organization_id is None
            or not isinstance(token, Token)
        ):
            await self.close(code=4401)
            return
        self.group_name = organization_group(user.organization_id)
        self.login_group = session_group(session_id_for(token))
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.channel_layer.group_add(self.login_group, self.channel_name)
        await self.accept(subprotocol="billable.v1")
        self.expiry_task = asyncio.create_task(self.expire_at(token["exp"]))

    async def expire_at(self, expiry: int) -> None:
        await asyncio.sleep(max(0, expiry - time.time()))
        await self.close(code=4401)

    async def deny_session(self) -> None:
        await self.send_json({"event": "session.revoked", "payload": {}})
        await self.close(code=4401)

    async def disconnect(self, code: int) -> None:
        if self.expiry_task is not None:
            self.expiry_task.cancel()
            with suppress(asyncio.CancelledError):
                await self.expiry_task
        for group in (self.group_name, self.login_group):
            if group is not None:
                await self.channel_layer.group_discard(group, self.channel_name)

    async def authorized_user(self) -> User | None:
        token = self.scope.get("auth_token")
        if not isinstance(token, Token) or token["exp"] <= time.time():
            await self.close(code=4401)
            return None
        try:
            user = await database_sync_to_async(SessionJWTAuthentication().get_user)(token)
        except AuthenticationFailed:
            await self.deny_session()
            return None
        if (
            not isinstance(user, User)
            or user.organization_id is None
            or organization_group(user.organization_id) != self.group_name
        ):
            await self.close(code=4403)
            return None
        return user

    async def receive(
        self, text_data: str | None = None, bytes_data: bytes | None = None, **kwargs: Any
    ) -> None:
        if bytes_data is not None or text_data is None or len(text_data.encode()) > 4096:
            await self.close(code=1009)
            return
        try:
            await super().receive(text_data=text_data, **kwargs)
        except ValueError:
            await self.close(code=1003)

    async def receive_json(self, content: Any, **kwargs: Any) -> None:
        if not isinstance(content, dict) or content != {"type": "ping"}:
            await self.close(code=1008)
            return
        now = time.monotonic()
        if now - self.last_ping < 1:
            await self.close(code=1008)
            return
        self.last_ping = now
        if await self.authorized_user() is not None:
            await self.send_json({"event": "pong", "payload": {}})

    async def session_revoked(self, message: dict[str, Any]) -> None:
        await self.deny_session()

    async def organization_event(self, message: dict[str, Any]) -> None:
        user = await self.authorized_user()
        if user is None:
            return
        event, payload = message["event"], message["payload"]
        if event == "invoice.changed" and not user.is_manager:
            return
        if event in {"entry.changed", "entry.deleted"} and not user.is_manager:
            owner_id = payload.get("user_id")
            if event == "entry.changed":
                owner_id = payload.get("entry", {}).get("user", {}).get("id")
            if owner_id != user.pk:
                await self.send_json({"event": "activity.changed", "payload": {}})
                return
        await self.send_json({"event": event, "payload": payload})
