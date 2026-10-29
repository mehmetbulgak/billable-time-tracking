import { parseActivityEvent, type ActivityEvent } from "./activityEvents";

export type ConnectionStatus = "connecting" | "online" | "offline";

interface ActivityConnectionOptions {
  getToken: () => string | null;
  refreshSession: () => void;
  onStatus: (status: ConnectionStatus) => void;
  onEvent: (event: ActivityEvent) => void;
  onReconnect: () => void;
}

const RECONNECT_BASE_MS = 1000;
const RECONNECT_MAX_MS = 30_000;
const PING_INTERVAL_MS = 25_000;

export function activitySocketUrl(token: string, location: Location = window.location): string {
  const origin =
    import.meta.env.VITE_WS_URL ??
    `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}`;
  return `${origin.replace(/\/$/, "")}/ws/activity/?token=${encodeURIComponent(token)}`;
}

export function createActivityConnection({
  getToken,
  refreshSession,
  onStatus,
  onEvent,
  onReconnect,
}: ActivityConnectionOptions): () => void {
  let socket: WebSocket | null = null;
  let attempts = 0;
  let reconnectTimer: number | undefined;
  let pingTimer: number | undefined;
  let disposed = false;
  let hasConnected = false;

  const scheduleReconnect = () => {
    const delay = Math.min(RECONNECT_MAX_MS, RECONNECT_BASE_MS * 2 ** attempts);
    attempts += 1;
    reconnectTimer = window.setTimeout(connect, delay);
  };

  function connect() {
    if (disposed) {
      return;
    }
    const token = getToken();
    if (!token) {
      refreshSession();
      scheduleReconnect();
      return;
    }

    let opened = false;
    const connection = new WebSocket(activitySocketUrl(token));
    socket = connection;
    connection.addEventListener("open", () => {
      if (disposed || socket !== connection) {
        return;
      }
      opened = true;
      attempts = 0;
      onStatus("online");
      if (hasConnected) {
        onReconnect();
      }
      hasConnected = true;
      pingTimer = window.setInterval(() => {
        if (connection.readyState === WebSocket.OPEN) {
          connection.send(JSON.stringify({ type: "ping" }));
        }
      }, PING_INTERVAL_MS);
    });
    connection.addEventListener("message", (message: MessageEvent<unknown>) => {
      if (disposed || socket !== connection || typeof message.data !== "string") {
        return;
      }
      const event = parseActivityEvent(message.data);
      if (event) {
        onEvent(event);
      }
    });
    connection.addEventListener("close", () => {
      if (disposed || socket !== connection) {
        return;
      }
      window.clearInterval(pingTimer);
      onStatus("offline");
      if (!opened) {
        refreshSession();
      }
      scheduleReconnect();
    });
  }

  connect();

  return () => {
    disposed = true;
    window.clearTimeout(reconnectTimer);
    window.clearInterval(pingTimer);
    socket?.close();
  };
}
