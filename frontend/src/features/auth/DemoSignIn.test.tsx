import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router";
import { RequireAuth } from "./RequireAuth";
import { StrictMode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { json, mockFetch, renderWithProviders, route } from "@/test/render";

import { DemoSignIn } from "./DemoSignIn";

afterEach(() => {
  vi.unstubAllGlobals();
  window.localStorage.clear();
});

describe("demo entry", () => {
  it("opens one manager session without a form, including in Strict Mode", async () => {
    const { fetchMock, calls } = mockFetch(
      route("POST", "/api/v1/auth/token/", () => json({ access: "demo", csrf_token: "csrf" })),
    );
    vi.stubGlobal("fetch", fetchMock);
    const { store } = renderWithProviders(
      <StrictMode>
        <DemoSignIn />
      </StrictMode>,
    );

    await waitFor(() => {
      expect(store.getState().auth.accessToken).toBe("demo");
    });
    expect(calls.filter((call) => call.method === "POST")).toHaveLength(1);
    expect(await calls.find((call) => call.method === "POST")?.json()).toEqual({
      email: "can@northwind.test",
      password: "billable-demo",
    });
  });

  it("lets a visitor retry after a temporary server error", async () => {
    let attempts = 0;
    const { fetchMock } = mockFetch(
      route("POST", "/api/v1/auth/token/", () =>
        ++attempts === 1
          ? json({ detail: "Starting demo. Please try again." }, 503)
          : json({ access: "demo", csrf_token: "csrf" }),
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const { store } = renderWithProviders(<DemoSignIn />);

    await userEvent.click(await screen.findByRole("button", { name: "Try again" }));
    await waitFor(() => {
      expect(store.getState().auth.accessToken).toBe("demo");
    });
    expect(attempts).toBe(2);
  });
});

it("does not sign a visitor back in after the session is revoked", async () => {
  vi.stubEnv("VITE_DEMO_MODE", "true");
  const { fetchMock, calls } = mockFetch();
  vi.stubGlobal("fetch", fetchMock);
  renderWithProviders(
    <Routes>
      <Route path="/" element={<RequireAuth />} />
      <Route path="/login" element={<div>Signed out</div>} />
    </Routes>,
    {
      preloadedState: {
        auth: { accessToken: null, csrfToken: null, hasSession: false, sessionVersion: 1 },
      },
    },
  );
  expect(await screen.findByText("Signed out")).toBeInTheDocument();
  expect(calls).toHaveLength(0);
  vi.unstubAllEnvs();
});
