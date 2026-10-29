import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { buildEntry } from "@/test/fixtures";
import { json, mockFetch, renderWithProviders, route } from "@/test/render";

import { TimerBar } from "./TimerBar";

const authenticated = {
  auth: { accessToken: "access", csrfToken: "csrf", hasSession: true, sessionVersion: 0 },
};

describe("TimerBar", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it("shows the running timer and stops it", async () => {
    const startedAt = new Date(Date.now() - 65 * 60 * 1000).toISOString();
    const running = buildEntry({ started_at: startedAt, ended_at: null, is_running: true });
    const { fetchMock, calls } = mockFetch(
      route("GET", "/api/v1/time-entries/current/", () => json(running)),
      route("POST", "/api/v1/time-entries/stop/", () =>
        json({
          ...running,
          ended_at: new Date().toISOString(),
          is_running: false,
          duration_seconds: 3900,
        }),
      ),
      route("GET", "/api/v1/time-entries/active/", () => json([])),
      route("GET", "/api/v1/time-entries/", () =>
        json({ count: 0, next: null, previous: null, results: [] }),
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    renderWithProviders(<TimerBar />, { preloadedState: authenticated });

    expect(await screen.findByText("Packaging mockups")).toBeInTheDocument();
    expect(screen.getByLabelText("Elapsed time")).toHaveTextContent(/^1:0[45]:\d{2}$/);
    expect(calls[0]?.headers.get("Authorization")).toBe("Bearer access");

    await user.click(screen.getByRole("button", { name: "Stop" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Start" })).toBeInTheDocument();
    });
    expect(
      calls.some((call) => call.method === "POST" && call.url.endsWith("/time-entries/stop/")),
    ).toBe(true);
  });

  it("asks for a project before starting", async () => {
    const { fetchMock, calls } = mockFetch(
      route("GET", "/api/v1/time-entries/current/", () => new Response(null, { status: 204 })),
      route("GET", "/api/v1/projects/", () =>
        json({ count: 0, next: null, previous: null, results: [] }),
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    const { store } = renderWithProviders(<TimerBar />, { preloadedState: authenticated });

    await user.click(await screen.findByRole("button", { name: "Start" }));

    expect(store.getState().notifications.queue[0]?.message).toBe(
      "Choose a project to start the timer.",
    );
    expect(calls.some((call) => call.method === "POST")).toBe(false);
  });
});
