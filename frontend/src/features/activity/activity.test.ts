import { waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { makeStore } from "@/app/store";
import { timeEntriesApi } from "@/features/timeEntries/timeEntriesApi";
import { buildEntry } from "@/test/fixtures";
import { json, mockFetch, route } from "@/test/render";

import { mergeActiveTimer } from "./activeTimers";
import { parseActivityEvent } from "./activityEvents";
import { activitySocketUrl } from "./activityConnection";
import { applyActivityEvent } from "./applyActivityEvent";

describe("parseActivityEvent", () => {
  it("accepts well-formed timer events", () => {
    const entry = buildEntry({ ended_at: null, is_running: true });

    const event = parseActivityEvent(
      JSON.stringify({ event: "timer.started", payload: { entry } }),
    );

    expect(event).toEqual({ event: "timer.started", payload: { entry } });
  });

  it.each([
    "not json",
    JSON.stringify({ event: "timer.started", payload: {} }),
    JSON.stringify({ event: "unknown", payload: {} }),
  ])("rejects malformed messages: %s", (raw) => {
    expect(parseActivityEvent(raw)).toBeNull();
  });
});

describe("mergeActiveTimer", () => {
  const elif = { id: 3, email: "elif@northwind.test", full_name: "Elif Şahin" };

  it("adds a newly started timer in start order", () => {
    const existing = buildEntry({
      id: 1,
      started_at: "2026-03-02T09:00:00",
      is_running: true,
      ended_at: null,
    });
    const started = buildEntry({
      id: 2,
      user: elif,
      started_at: "2026-03-02T08:00:00",
      is_running: true,
      ended_at: null,
    });

    expect(mergeActiveTimer([existing], started).map((timer) => timer.id)).toEqual([2, 1]);
  });

  it("replaces the previous timer of the same person", () => {
    const previous = buildEntry({ id: 1, is_running: true, ended_at: null });
    const next = buildEntry({ id: 2, is_running: true, ended_at: null });

    expect(mergeActiveTimer([previous], next).map((timer) => timer.id)).toEqual([2]);
  });

  it("removes stopped timers", () => {
    const running = buildEntry({ id: 1, is_running: true, ended_at: null });

    expect(mergeActiveTimer([running], { ...running, is_running: false })).toEqual([]);
  });
});

describe("activitySocketUrl", () => {
  it("uses a secure socket without a token in the URL", () => {
    const location = { protocol: "https:", host: "app.billable.test" } as Location;

    expect(activitySocketUrl(location)).toBe("wss://app.billable.test/ws/activity/");
  });
});

describe("activity cache", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("refreshes the team view when a running entry changes", async () => {
    const initial = buildEntry({ is_running: true, ended_at: null });
    const updated = { ...initial, description: "Updated on another device" };
    let requests = 0;
    const { fetchMock } = mockFetch(
      route("GET", "/api/v1/time-entries/active/", () => {
        requests += 1;
        return json([requests === 1 ? initial : updated]);
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const store = makeStore({
      auth: { accessToken: "access", csrfToken: "csrf", hasSession: true, sessionVersion: 0 },
    });
    const subscription = store.dispatch(timeEntriesApi.endpoints.getActiveTimers.initiate());
    await subscription;

    store.dispatch(applyActivityEvent({ event: "entry.changed", payload: { entry: updated } }));

    await waitFor(() => {
      const timers = timeEntriesApi.endpoints.getActiveTimers.select()(store.getState()).data;
      expect(timers?.[0]?.description).toBe(updated.description);
    });
    subscription.unsubscribe();
  });
});
