import {
  fetchBaseQuery,
  type BaseQueryApi,
  type BaseQueryFn,
  type FetchArgs,
  type FetchBaseQueryError,
} from "@reduxjs/toolkit/query/react";

import { type AuthState, csrfReceived, loggedOut, tokensReceived } from "@/features/auth/authSlice";

import { isAccessSession, isRecord } from "./guards";

interface StateWithAuth {
  auth: AuthState;
}

type RefreshResult = { accessToken: string } | { error: FetchBaseQueryError };
type CSRFResult = { token: string } | { error: FetchBaseQueryError };

const stateOf = (api: Pick<BaseQueryApi, "getState">): AuthState =>
  (api.getState() as StateWithAuth).auth;

const pendingRefreshes = new WeakMap<BaseQueryApi["getState"], Promise<RefreshResult>>();
const pendingCSRF = new WeakMap<BaseQueryApi["getState"], Promise<CSRFResult>>();
const rawBaseQuery = fetchBaseQuery({
  baseUrl: import.meta.env.VITE_API_URL ?? "/api/v1",
  credentials: "include",
  prepareHeaders: (headers, api) => {
    const { accessToken, csrfToken } = stateOf(api);
    if (accessToken) {
      headers.set("Authorization", `Bearer ${accessToken}`);
    }
    if (csrfToken) {
      headers.set("X-CSRFToken", csrfToken);
    }
    return headers;
  },
});

const sessionChanged = (): { error: FetchBaseQueryError } => ({
  error: { status: 401, data: { detail: "The session has changed. Please sign in again." } },
});

async function loadCSRF(api: BaseQueryApi, extraOptions: object): Promise<CSRFResult> {
  const version = stateOf(api).sessionVersion;
  const response = await rawBaseQuery("/auth/csrf/", api, extraOptions);
  if (stateOf(api).sessionVersion !== version) {
    return sessionChanged();
  }
  if (isRecord(response.data) && typeof response.data.csrf_token === "string") {
    api.dispatch(csrfReceived(response.data.csrf_token));
    return { token: response.data.csrf_token };
  }
  return {
    error: response.error ?? { status: "CUSTOM_ERROR", error: "Invalid CSRF response." },
  };
}

async function ensureCSRF(
  api: BaseQueryApi,
  extraOptions: object,
  force = false,
): Promise<CSRFResult> {
  const { csrfToken } = stateOf(api);
  if (csrfToken && !force) {
    return { token: csrfToken };
  }
  const pending = pendingCSRF.get(api.getState);
  if (pending) {
    return pending;
  }
  const request = loadCSRF(api, extraOptions).finally(() => pendingCSRF.delete(api.getState));
  pendingCSRF.set(api.getState, request);
  return request;
}

async function csrfQuery(args: string | FetchArgs, api: BaseQueryApi, extraOptions: object) {
  const csrf = await ensureCSRF(api, extraOptions);
  if ("error" in csrf) {
    return { error: csrf.error };
  }
  const result = await rawBaseQuery(args, api, extraOptions);
  if (result.error?.status !== 403) {
    return result;
  }
  const updated = await ensureCSRF(api, extraOptions, true);
  return "error" in updated ? { error: updated.error } : rawBaseQuery(args, api, extraOptions);
}

async function refreshTokens(api: BaseQueryApi, extraOptions: object): Promise<RefreshResult> {
  const { hasSession, sessionVersion } = stateOf(api);
  if (!hasSession) {
    return sessionChanged();
  }
  const response = await csrfQuery(
    { url: "/auth/token/refresh/", method: "POST", body: {} },
    api,
    extraOptions,
  );
  if (!stateOf(api).hasSession || stateOf(api).sessionVersion !== sessionVersion) {
    return sessionChanged();
  }
  if (isAccessSession(response.data)) {
    api.dispatch(tokensReceived(response.data));
    return { accessToken: response.data.access };
  }
  if (response.error?.status === 401) {
    api.dispatch(loggedOut());
  }
  return {
    error: response.error ?? { status: "CUSTOM_ERROR", error: "Invalid session response." },
  };
}

function sharedRefresh(api: BaseQueryApi, extraOptions: object): Promise<RefreshResult> {
  const pending = pendingRefreshes.get(api.getState);
  if (pending) {
    return pending;
  }
  const refresh = refreshTokens(api, extraOptions).finally(() =>
    pendingRefreshes.delete(api.getState),
  );
  pendingRefreshes.set(api.getState, refresh);
  return refresh;
}

export const authenticatedQuery: BaseQueryFn<
  string | FetchArgs,
  unknown,
  FetchBaseQueryError
> = async (args, api, extraOptions) => {
  const path = typeof args === "string" ? args : args.url;
  if (path.startsWith("/auth/token/") || path === "/auth/logout/") {
    return csrfQuery(args, api, extraOptions);
  }
  const pending = pendingRefreshes.get(api.getState);
  if (pending || (!stateOf(api).accessToken && stateOf(api).hasSession)) {
    const refreshed = await (pending ?? sharedRefresh(api, extraOptions));
    if ("error" in refreshed) {
      return { error: refreshed.error };
    }
  }
  const { accessToken, sessionVersion, hasSession } = stateOf(api);
  const result = await rawBaseQuery(args, api, extraOptions);
  if (result.error?.status !== 401) {
    return result;
  }
  const current = stateOf(api);
  if (current.accessToken && current.accessToken !== accessToken) {
    return rawBaseQuery(args, api, extraOptions);
  }
  if (!hasSession || !current.hasSession || current.sessionVersion !== sessionVersion) {
    return result;
  }
  const refreshed = await sharedRefresh(api, extraOptions);
  return "error" in refreshed ? { error: refreshed.error } : rawBaseQuery(args, api, extraOptions);
};
