import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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
      route("POST", "/api/v1/auth/token/", () => json({ access: "demo", refresh: "demo-refresh" })),
    );
    vi.stubGlobal("fetch", fetchMock);
    const { store } = renderWithProviders(
      <StrictMode>
        <DemoSignIn />
      </StrictMode>,
    );

    await waitFor(() => expect(store.getState().auth.accessToken).toBe("demo"));
    expect(calls).toHaveLength(1);
    expect(await calls[0]?.json()).toEqual({
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
          : json({ access: "demo", refresh: "demo-refresh" }),
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const { store } = renderWithProviders(<DemoSignIn />);

    await userEvent.click(await screen.findByRole("button", { name: "Try again" }));
    await waitFor(() => expect(store.getState().auth.accessToken).toBe("demo"));
    expect(attempts).toBe(2);
  });
});
