import { describe, expect, it } from "vitest";

import { buildEntry } from "@/test/fixtures";

import { mergeActiveTimer } from "./activeTimers";
import { parseActivityEvent } from "./activityEvents";
import { activitySocketUrl } from "./useActivityStream";

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
  it("uses a secure socket on https pages and escapes the token", () => {
    const location = { protocol: "https:", host: "app.billable.test" } as Location;

    expect(activitySocketUrl("a b", location)).toBe(
      "wss://app.billable.test/ws/activity/?token=a%20b",
    );
  });
});
