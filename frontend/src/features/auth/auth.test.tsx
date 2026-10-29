import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { makeStore } from "@/app/store";
import { managerUser } from "@/test/fixtures";
import { timeEntriesApi } from "@/features/timeEntries/timeEntriesApi";
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

  it("keeps the session after a temporary refresh failure and permits retry", async () => {
    tokenStorage.write("stored-refresh");
    let attempts = 0;
    const { fetchMock, calls } = mockFetch(
      route("POST", "/api/v1/auth/token/refresh/", () => {
        attempts += 1;
        return attempts === 1
          ? json({ detail: "Temporarily unavailable" }, 503)
          : json({ access: "fresh-access", refresh: "rotated-refresh" });
      }),
      route("GET", "/api/v1/auth/me/", () => json(managerUser)),
    );
    vi.stubGlobal("fetch", fetchMock);
    const store = makeStore();

    const failed = await store.dispatch(authApi.endpoints.getCurrentUser.initiate());

    expect(failed.error).toMatchObject({ status: 503 });
    expect(tokenStorage.read()).toBe("stored-refresh");
    expect(calls).toHaveLength(1);

    const retried = await store.dispatch(
      authApi.endpoints.getCurrentUser.initiate(undefined, { forceRefetch: true }),
    );

    expect(retried.data?.email).toBe(managerUser.email);
    expect(tokenStorage.read()).toBe("rotated-refresh");
  });

  it("shares one refresh between concurrent requests in the same store", async () => {
    tokenStorage.write("stored-refresh");
    const { fetchMock, calls } = mockFetch(
      route("POST", "/api/v1/auth/token/refresh/", () =>
        json({ access: "fresh-access", refresh: "rotated-refresh" }),
      ),
      route("GET", "/api/v1/auth/me/", () => json(managerUser)),
      route("GET", "/api/v1/time-entries/active/", () => json([])),
    );
    vi.stubGlobal("fetch", fetchMock);
    const store = makeStore();

    await Promise.all([
      store.dispatch(authApi.endpoints.getCurrentUser.initiate()),
      store.dispatch(timeEntriesApi.endpoints.getActiveTimers.initiate()),
    ]);

    expect(calls.filter((call) => call.url.includes("/token/refresh/"))).toHaveLength(1);
  });

  it("does not share refreshes between independent stores", async () => {
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
    const first = makeStore({ auth: { accessToken: null, refreshToken: "first" } });
    const second = makeStore({ auth: { accessToken: null, refreshToken: "second" } });

    const responses = await Promise.all([
      first.dispatch(authApi.endpoints.getCurrentUser.initiate()),
      second.dispatch(authApi.endpoints.getCurrentUser.initiate()),
    ]);

    expect(responses.every((response) => response.data?.email === managerUser.email)).toBe(true);
    expect(calls.filter((call) => call.url.includes("/token/refresh/"))).toHaveLength(2);
  });

  it("does not restore a logged-out session when a refresh finishes late", async () => {
    let completeRefresh: (response: Response) => void = () => undefined;
    const refreshResponse = new Promise<Response>((resolve) => {
      completeRefresh = resolve;
    });
    const fetchMock = vi.fn(() => refreshResponse);
    vi.stubGlobal("fetch", fetchMock);
    const store = makeStore({ auth: { accessToken: null, refreshToken: "stored-refresh" } });
    const request = store.dispatch(authApi.endpoints.getCurrentUser.initiate());
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledOnce();
    });

    store.dispatch(loggedOut());
    completeRefresh(json({ access: "late-access", refresh: "late-refresh" }));
    await request;

    expect(store.getState().auth).toEqual({ accessToken: null, refreshToken: null });
    expect(tokenStorage.read()).toBeNull();
  });

  it("retries a late unauthorized response with tokens refreshed by another request", async () => {
    let finishOldRequest: (response: Response) => void = () => undefined;
    const oldResponse = new Promise<Response>((resolve) => {
      finishOldRequest = resolve;
    });
    let refreshes = 0;
    let oldRequests = 0;
    vi.stubGlobal("fetch", async (request: Request) => {
      const path = new URL(request.url).pathname;
      if (path.endsWith("/token/refresh/")) {
        refreshes += 1;
        return json({ access: "fresh-access", refresh: "rotated-refresh" });
      }
      if (request.headers.get("Authorization") === "Bearer expired-access") {
        oldRequests += 1;
        return path.endsWith("/active/") ? oldResponse : json({ detail: "Expired" }, 401);
      }
      return json(path.endsWith("/active/") ? [] : managerUser);
    });
    const store = makeStore({
      auth: { accessToken: "expired-access", refreshToken: "stored-refresh" },
    });
    const profile = store.dispatch(authApi.endpoints.getCurrentUser.initiate());
    const timers = store.dispatch(timeEntriesApi.endpoints.getActiveTimers.initiate());
    await waitFor(() => {
      expect(oldRequests).toBe(2);
      expect(store.getState().auth.accessToken).toBe("fresh-access");
    });

    finishOldRequest(json({ detail: "Expired" }, 401));
    const responses = await Promise.all([profile, timers]);

    expect(responses.every((response) => response.isSuccess)).toBe(true);
    expect(refreshes).toBe(1);
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
