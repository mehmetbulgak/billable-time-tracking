import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { createActivityConnection, type ConnectionStatus } from "./activityConnection";

class TestSocket extends EventTarget {
  static OPEN = 1;
  static instances: TestSocket[] = [];
  readyState = 0;
  send = vi.fn<(message: string) => void>();

  constructor(readonly url: string) {
    super();
    TestSocket.instances.push(this);
  }

  open() {
    this.readyState = TestSocket.OPEN;
    this.dispatchEvent(new Event("open"));
  }

  close() {
    this.readyState = 3;
    this.dispatchEvent(new Event("close"));
  }
}

const disposers: (() => void)[] = [];

beforeEach(() => {
  vi.useFakeTimers();
  TestSocket.instances = [];
  vi.stubGlobal("WebSocket", TestSocket);
});

afterEach(() => {
  disposers.splice(0).forEach((dispose) => {
    dispose();
  });
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

function connect(getToken: () => string | null = () => "access") {
  const callbacks = {
    getToken,
    refreshSession: vi.fn(),
    onStatus: vi.fn<(status: ConnectionStatus) => void>(),
    onEvent: vi.fn(),
    onReconnect: vi.fn(),
  };
  const dispose = createActivityConnection(callbacks);
  disposers.push(dispose);
  return { ...callbacks, dispose };
}

function latestSocket(): TestSocket {
  const socket = TestSocket.instances.at(-1);
  if (!socket) {
    throw new Error("No socket was created.");
  }
  return socket;
}

describe("activity connection", () => {
  it("resynchronizes after reconnection and uses the latest access token", () => {
    let token = "first";
    const callbacks = connect(() => token);
    latestSocket().open();
    expect(callbacks.onReconnect).not.toHaveBeenCalled();

    latestSocket().close();
    token = "refreshed";
    vi.advanceTimersByTime(1000);
    expect(latestSocket().url).toContain("token=refreshed");
    latestSocket().open();

    expect(callbacks.onReconnect).toHaveBeenCalledOnce();
    expect(callbacks.onStatus.mock.calls.map(([status]) => status)).toEqual([
      "online",
      "offline",
      "online",
    ]);
  });

  it("ignores messages and late open events after disposal", () => {
    const callbacks = connect();
    const socket = latestSocket();
    callbacks.dispose();

    socket.open();
    socket.dispatchEvent(
      new MessageEvent("message", {
        data: JSON.stringify({ event: "pong", payload: {} }),
      }),
    );
    vi.advanceTimersByTime(60_000);

    expect(callbacks.onStatus).not.toHaveBeenCalled();
    expect(callbacks.onEvent).not.toHaveBeenCalled();
    expect(socket.send).not.toHaveBeenCalled();
    expect(TestSocket.instances).toHaveLength(1);
    expect(vi.getTimerCount()).toBe(0);
  });

  it("sends heartbeats only while the socket is open", () => {
    connect();
    const socket = latestSocket();
    socket.open();
    vi.advanceTimersByTime(25_000);
    expect(socket.send).toHaveBeenCalledWith(JSON.stringify({ type: "ping" }));

    socket.readyState = 2;
    vi.advanceTimersByTime(25_000);

    expect(socket.send).toHaveBeenCalledOnce();
  });

  it("backs off after failed connections and stops retrying on disposal", () => {
    const callbacks = connect();
    latestSocket().close();
    vi.advanceTimersByTime(999);
    expect(TestSocket.instances).toHaveLength(1);
    vi.advanceTimersByTime(1);
    latestSocket().close();
    vi.advanceTimersByTime(1999);
    expect(TestSocket.instances).toHaveLength(2);

    callbacks.dispose();
    vi.advanceTimersByTime(30_000);

    expect(TestSocket.instances).toHaveLength(2);
    expect(callbacks.refreshSession).toHaveBeenCalledTimes(2);
    expect(vi.getTimerCount()).toBe(0);
  });

  it("requests a session refresh before reconnecting without an access token", () => {
    let token: string | null = null;
    const callbacks = connect(() => token);
    expect(callbacks.refreshSession).toHaveBeenCalledOnce();
    expect(TestSocket.instances).toHaveLength(0);

    token = "ready";
    vi.advanceTimersByTime(1000);

    expect(latestSocket().url).toContain("token=ready");
  });
});
