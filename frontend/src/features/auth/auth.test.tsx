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
import { sessionPersistence } from "./sessionPersistence";

describe("auth state", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("persists only a session flag and clears legacy tokens", () => {
    const store = makeStore();

    store.dispatch(tokensReceived({ access: "access-1", csrf_token: "csrf" }));
    expect(store.getState().auth).toEqual({
      accessToken: "access-1",
      csrfToken: "csrf",
      hasSession: true,
      sessionVersion: 1,
    });
    expect(sessionPersistence.read()).toBe(true);
    expect(window.localStorage.getItem("billable.refreshToken")).toBeNull();
    expect(window.localStorage.getItem("billable.hasSession")).toBe("1");

    store.dispatch(loggedOut());
    expect(store.getState().auth.hasSession).toBe(false);
    expect(sessionPersistence.read()).toBe(false);
  });
});

describe("session restore", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    window.localStorage.clear();
  });

  it("restores a session using the HttpOnly cookie", async () => {
    sessionPersistence.write();
    const { fetchMock, calls } = mockFetch(
      route("POST", "/api/v1/auth/token/refresh/", () =>
        json({ access: "fresh-access", csrf_token: "csrf" }),
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
      "/api/v1/auth/csrf/",
      "/api/v1/auth/token/refresh/",
      "/api/v1/auth/me/",
    ]);
    expect(sessionPersistence.read()).toBe(true);
  });

  it("logs out when the stored session is rejected", async () => {
    sessionPersistence.write();
    const { fetchMock } = mockFetch(
      route("POST", "/api/v1/auth/token/refresh/", () =>
        json({ detail: "Token is invalid or expired" }, 401),
      ),
      route("GET", "/api/v1/auth/me/", () => json({ detail: "Not authenticated" }, 401)),
    );
    vi.stubGlobal("fetch", fetchMock);
    const store = makeStore();

    await store.dispatch(authApi.endpoints.getCurrentUser.initiate());

    expect(store.getState().auth.hasSession).toBe(false);
    expect(sessionPersistence.read()).toBe(false);
  });

  it("keeps the session after a temporary refresh failure and permits retry", async () => {
    sessionPersistence.write();
    let attempts = 0;
    const { fetchMock, calls } = mockFetch(
      route("POST", "/api/v1/auth/token/refresh/", () => {
        attempts += 1;
        return attempts === 1
          ? json({ detail: "Temporarily unavailable" }, 503)
          : json({ access: "fresh-access", csrf_token: "csrf" });
      }),
      route("GET", "/api/v1/auth/me/", () => json(managerUser)),
    );
    vi.stubGlobal("fetch", fetchMock);
    const store = makeStore();

    const failed = await store.dispatch(authApi.endpoints.getCurrentUser.initiate());

    expect(failed.error).toMatchObject({ status: 503 });
    expect(sessionPersistence.read()).toBe(true);
    expect(calls).toHaveLength(2);

    const retried = await store.dispatch(
      authApi.endpoints.getCurrentUser.initiate(undefined, { forceRefetch: true }),
    );

    expect(retried.data?.email).toBe(managerUser.email);
    expect(sessionPersistence.read()).toBe(true);
  });

  it("shares one refresh between concurrent requests in the same store", async () => {
    sessionPersistence.write();
    const { fetchMock, calls } = mockFetch(
      route("POST", "/api/v1/auth/token/refresh/", () =>
        json({ access: "fresh-access", csrf_token: "csrf" }),
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
        json({ access: "fresh-access", csrf_token: "csrf" }),
      ),
      route("GET", "/api/v1/auth/me/", (request) =>
        request.headers.get("Authorization") === "Bearer fresh-access"
          ? json(managerUser)
          : json({ detail: "Not authenticated" }, 401),
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const first = makeStore({
      auth: { accessToken: null, csrfToken: "csrf", hasSession: true, sessionVersion: 0 },
    });
    const second = makeStore({
      auth: { accessToken: null, csrfToken: "csrf", hasSession: true, sessionVersion: 0 },
    });

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
    const store = makeStore({
      auth: { accessToken: null, csrfToken: "csrf", hasSession: true, sessionVersion: 0 },
    });
    const request = store.dispatch(authApi.endpoints.getCurrentUser.initiate());
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledOnce();
    });

    store.dispatch(loggedOut());
    completeRefresh(json({ access: "late-access", csrf_token: "csrf" }));
    await request;

    expect(store.getState().auth).toMatchObject({
      accessToken: null,
      csrfToken: null,
      hasSession: false,
    });
    expect(sessionPersistence.read()).toBe(false);
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
        return json({ access: "fresh-access", csrf_token: "csrf" });
      }
      if (request.headers.get("Authorization") === "Bearer expired-access") {
        oldRequests += 1;
        return path.endsWith("/active/") ? oldResponse : json({ detail: "Expired" }, 401);
      }
      return json(path.endsWith("/active/") ? [] : managerUser);
    });
    const store = makeStore({
      auth: {
        accessToken: "expired-access",
        csrfToken: "csrf",
        hasSession: true,
        sessionVersion: 0,
      },
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
        json({ access: "access-token", csrf_token: "csrf" }),
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
    expect(await calls.find((call) => call.method === "POST")?.json()).toEqual({
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

describe("cookie session security", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    window.localStorage.clear();
  });

  it("removes refresh tokens left by an older version", () => {
    window.localStorage.setItem("billable.refreshToken", "legacy-secret");
    makeStore();
    expect(window.localStorage.getItem("billable.refreshToken")).toBeNull();
  });

  it("requests cookies and a CSRF token without sending a refresh token in JSON", async () => {
    sessionPersistence.write();
    const { fetchMock, calls } = mockFetch(
      route("POST", "/api/v1/auth/token/refresh/", () =>
        json({ access: "new", csrf_token: "csrf" }),
      ),
      route("GET", "/api/v1/auth/me/", () => json(managerUser)),
    );
    vi.stubGlobal("fetch", fetchMock);
    await makeStore().dispatch(authApi.endpoints.getCurrentUser.initiate());
    const refresh = calls.find((request) => request.url.endsWith("/token/refresh/"));
    expect(refresh?.credentials).toBe("include");
    expect(refresh?.headers.get("X-CSRFToken")).toBe("csrf");
    expect(await refresh?.json()).toEqual({});
  });

  it("keeps the session when the server cannot confirm logout", async () => {
    const { fetchMock } = mockFetch(
      route("POST", "/api/v1/auth/logout/", () => json({ detail: "Unavailable" }, 503)),
    );
    vi.stubGlobal("fetch", fetchMock);
    const store = makeStore({
      auth: { accessToken: "access", csrfToken: "csrf", hasSession: true, sessionVersion: 0 },
    });
    await store.dispatch(authApi.endpoints.logout.initiate());
    expect(store.getState().auth.hasSession).toBe(true);
  });

  it("clears the browser session after server logout succeeds", async () => {
    const { fetchMock, calls } = mockFetch(
      route("POST", "/api/v1/auth/logout/", () => new Response(null, { status: 204 })),
    );
    vi.stubGlobal("fetch", fetchMock);
    const store = makeStore({
      auth: { accessToken: "access", csrfToken: "csrf", hasSession: true, sessionVersion: 0 },
    });
    await store.dispatch(authApi.endpoints.logout.initiate());
    expect(calls[0]?.headers.get("X-CSRFToken")).toBe("csrf");
    expect(store.getState().auth.hasSession).toBe(false);
  });

  it("renews a stale CSRF token once without dropping the session", async () => {
    let attempts = 0;
    const { fetchMock } = mockFetch(
      route("POST", "/api/v1/auth/token/refresh/", (request) => {
        attempts += 1;
        return request.headers.get("X-CSRFToken") === "fresh-csrf"
          ? json({ access: "new", csrf_token: "fresh-csrf" })
          : json({ detail: "CSRF failed" }, 403);
      }),
      route("GET", "/api/v1/auth/csrf/", () => json({ csrf_token: "fresh-csrf" })),
      route("GET", "/api/v1/auth/me/", () => json(managerUser)),
    );
    vi.stubGlobal("fetch", fetchMock);
    const store = makeStore({
      auth: { accessToken: null, csrfToken: "stale", hasSession: true, sessionVersion: 0 },
    });
    const response = await store.dispatch(authApi.endpoints.getCurrentUser.initiate());
    expect(response.isSuccess).toBe(true);
    expect(attempts).toBe(2);
    expect(store.getState().auth.hasSession).toBe(true);
  });
});
