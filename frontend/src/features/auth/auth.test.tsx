import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { makeStore } from "@/app/store";
import { managerUser } from "@/test/fixtures";
import { json, mockFetch, renderWithProviders, route } from "@/test/render";

import { authApi } from "./authApi";
import { loggedOut, tokensReceived } from "./authSlice";
import { LoginPage } from "./LoginPage";
import { tokenStorage } from "./tokenStorage";

describe("auth state", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("persists the refresh token and clears it on logout", () => {
    const store = makeStore();

    store.dispatch(tokensReceived({ access: "access-1", refresh: "refresh-1" }));
    expect(store.getState().auth).toEqual({ accessToken: "access-1", refreshToken: "refresh-1" });
    expect(tokenStorage.read()).toBe("refresh-1");

    store.dispatch(loggedOut());
    expect(store.getState().auth.refreshToken).toBeNull();
    expect(tokenStorage.read()).toBeNull();
  });
});

describe("session restore", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    window.localStorage.clear();
  });

  it("refreshes before the first request when only a refresh token is stored", async () => {
    tokenStorage.write("stored-refresh");
    const { fetchMock, calls } = mockFetch(
      route("POST", "/api/v1/auth/token/refresh/", () =>
        json({ access: "fresh-access", refresh: "rotated-refresh" }),
      ),
      route("GET", "/api/v1/auth/me/", (request) =>
        request.headers.get("Authorization") === "Bearer fresh-access"
          ? json(managerUser)
          : json({ detail: "Not authenticated" }, 401),
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const store = makeStore();

    const result = await store.dispatch(authApi.endpoints.getCurrentUser.initiate());

    expect(result.data?.email).toBe(managerUser.email);
    expect(calls.map((call) => new URL(call.url).pathname)).toEqual([
      "/api/v1/auth/token/refresh/",
      "/api/v1/auth/me/",
    ]);
    expect(tokenStorage.read()).toBe("rotated-refresh");
  });

  it("logs out when the stored refresh token is rejected", async () => {
    tokenStorage.write("expired-refresh");
    const { fetchMock } = mockFetch(
      route("POST", "/api/v1/auth/token/refresh/", () =>
        json({ detail: "Token is invalid or expired" }, 401),
      ),
      route("GET", "/api/v1/auth/me/", () => json({ detail: "Not authenticated" }, 401)),
    );
    vi.stubGlobal("fetch", fetchMock);
    const store = makeStore();

    await store.dispatch(authApi.endpoints.getCurrentUser.initiate());

    expect(store.getState().auth.refreshToken).toBeNull();
    expect(tokenStorage.read()).toBeNull();
  });
});

describe("LoginPage", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    window.localStorage.clear();
  });

  it("signs in with the demo manager account", async () => {
    const { fetchMock, calls } = mockFetch(
      route("POST", "/api/v1/auth/token/", () =>
        json({ access: "access-token", refresh: "refresh-token" }),
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    const { store } = renderWithProviders(<LoginPage />, { route: "/login" });

    await user.click(screen.getByRole("button", { name: "Manager" }));
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(store.getState().auth.accessToken).toBe("access-token");
    });
    expect(await calls[0]?.json()).toEqual({
      email: "can@northwind.test",
      password: "billable-demo",
    });
  });

  it("shows the server error for wrong credentials", async () => {
    const { fetchMock } = mockFetch(
      route("POST", "/api/v1/auth/token/", () =>
        json({ detail: "No active account found with the given credentials" }, 401),
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    renderWithProviders(<LoginPage />, { route: "/login" });

    await user.type(screen.getByLabelText(/email/i), "someone@example.test");
    await user.type(screen.getByLabelText(/password/i), "wrong-password");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(
      await screen.findByText("No active account found with the given credentials"),
    ).toBeInTheDocument();
  });

  it("validates the form before calling the API", async () => {
    const { fetchMock, calls } = mockFetch();
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    renderWithProviders(<LoginPage />, { route: "/login" });

    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByText("Enter a valid email address.")).toBeInTheDocument();
    expect(calls).toHaveLength(0);
  });
});
