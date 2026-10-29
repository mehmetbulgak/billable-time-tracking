import { useEffect, useState } from "react";

import { useAppDispatch, useAppSelector, useAppStore } from "@/app/hooks";
import { authApi } from "@/features/auth/authApi";
import { selectAccessToken, selectHasSession } from "@/features/auth/authSlice";

import { parseActivityEvent } from "./activityEvents";
import { applyActivityEvent } from "./applyActivityEvent";

export type ConnectionStatus = "connecting" | "online" | "offline";

const RECONNECT_BASE_MS = 1000;
const RECONNECT_MAX_MS = 30_000;
const PING_INTERVAL_MS = 25_000;

export function activitySocketUrl(token: string, location: Location = window.location): string {
  const origin =
    import.meta.env.VITE_WS_URL ??
    `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}`;
  return `${origin}/ws/activity/?token=${encodeURIComponent(token)}`;
}

export function useActivityStream(): ConnectionStatus {
  const dispatch = useAppDispatch();
  const store = useAppStore();
  const hasSession = useAppSelector(selectHasSession);
  const [status, setStatus] = useState<ConnectionStatus>("connecting");

  useEffect(() => {
    if (!hasSession) {
      return undefined;
    }

    let socket: WebSocket | null = null;
    let attempts = 0;
    let reconnectTimer: number | undefined;
    let pingTimer: number | undefined;
    let disposed = false;

    const refreshSession = () => {
      void dispatch(
        authApi.endpoints.getCurrentUser.initiate(undefined, {
          forceRefetch: true,
          subscribe: false,
        }),
      );
    };

    const scheduleReconnect = () => {
      const delay = Math.min(RECONNECT_MAX_MS, RECONNECT_BASE_MS * 2 ** attempts);
      attempts += 1;
      reconnectTimer = window.setTimeout(connect, delay);
    };

    function connect() {
      const token = selectAccessToken(store.getState());
      if (!token) {
        refreshSession();
        scheduleReconnect();
        return;
      }
      let opened = false;
      socket = new WebSocket(activitySocketUrl(token));
      socket.addEventListener("open", () => {
        opened = true;
        attempts = 0;
        setStatus("online");
        pingTimer = window.setInterval(() => {
          socket?.send(JSON.stringify({ type: "ping" }));
        }, PING_INTERVAL_MS);
      });
      socket.addEventListener("message", (message: MessageEvent<unknown>) => {
        if (typeof message.data !== "string") {
          return;
        }
        const event = parseActivityEvent(message.data);
        if (event) {
          dispatch(applyActivityEvent(event));
        }
      });
      socket.addEventListener("close", () => {
        window.clearInterval(pingTimer);
        if (disposed) {
          return;
        }
        setStatus("offline");
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
  }, [dispatch, hasSession, store]);

  return status;
}
