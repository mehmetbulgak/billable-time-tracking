import json
from typing import Any
from urllib.parse import urlsplit

from asgiref.testing import ApplicationCommunicator


class ActivitySocket(ApplicationCommunicator):
    def __init__(
        self,
        application: Any,
        path: str = "/ws/activity/",
        *,
        token: str | None = None,
        origin: str | None = "http://testserver",
    ) -> None:
        parsed = urlsplit(path)
        super().__init__(
            application,
            {
                "type": "websocket",
                "asgi": {"version": "3.0"},
                "path": parsed.path,
                "raw_path": parsed.path.encode(),
                "query_string": parsed.query.encode(),
                "headers": [(b"origin", origin.encode())] if origin else [],
                "subprotocols": ["billable.v1", f"bearer.{token}"] if token else [],
                "scheme": "ws",
                "server": ("testserver", 80),
                "client": ("127.0.0.1", 1234),
            },
        )

    async def connect(self) -> tuple[bool, Any]:
        await self.send_input({"type": "websocket.connect"})
        response = await self.receive_output()
        return response["type"] == "websocket.accept", response.get(
            "code", response.get("subprotocol")
        )

    async def send_json_to(self, data: Any) -> None:
        await self.send_input({"type": "websocket.receive", "text": json.dumps(data)})

    async def receive_json_from(self) -> Any:
        response = await self.receive_output()
        assert response["type"] == "websocket.send"
        return json.loads(response["text"])

    async def disconnect(self) -> None:
        await self.send_input({"type": "websocket.disconnect", "code": 1000})
        await self.wait()
