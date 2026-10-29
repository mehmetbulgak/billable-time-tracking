import {
  fetchBaseQuery,
  type BaseQueryApi,
  type BaseQueryFn,
  type FetchArgs,
  type FetchBaseQueryError,
} from "@reduxjs/toolkit/query/react";

import {
  type AuthState,
  loggedOut,
  selectAccessToken,
  selectRefreshToken,
  tokensReceived,
} from "@/features/auth/authSlice";

import { isTokenPair } from "./guards";

interface StateWithAuth {
  auth: AuthState;
}

type RefreshResult = { accessToken: string } | { error: FetchBaseQueryError };

const stateOf = (api: Pick<BaseQueryApi, "getState">): StateWithAuth =>
  api.getState() as StateWithAuth;

const AUTH_ENDPOINT_PREFIX = "/auth/token/";
const pendingRefreshes = new WeakMap<BaseQueryApi["getState"], Promise<RefreshResult>>();
const rawBaseQuery = fetchBaseQuery({
  baseUrl: import.meta.env.VITE_API_URL ?? "/api/v1",
  prepareHeaders: (headers, api) => {
    const token = selectAccessToken(stateOf(api));
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    return headers;
  },
});

const sessionChanged = (): RefreshResult => ({
  error: { status: 401, data: { detail: "The session has changed. Please sign in again." } },
});

async function refreshTokens(api: BaseQueryApi, extraOptions: object): Promise<RefreshResult> {
  const refreshToken = selectRefreshToken(stateOf(api));
  if (!refreshToken) {
    return sessionChanged();
  }
  const response = await rawBaseQuery(
    { url: `${AUTH_ENDPOINT_PREFIX}refresh/`, method: "POST", body: { refresh: refreshToken } },
    api,
    extraOptions,
  );
  if (selectRefreshToken(stateOf(api)) !== refreshToken) {
    return sessionChanged();
  }
  if (isTokenPair(response.data)) {
    api.dispatch(tokensReceived(response.data));
    return { accessToken: response.data.access };
  }
  if (response.error?.status === 401 || response.error?.status === 403) {
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
  const refresh = refreshTokens(api, extraOptions).finally(() => {
    pendingRefreshes.delete(api.getState);
  });
  pendingRefreshes.set(api.getState, refresh);
  return refresh;
}

export const authenticatedQuery: BaseQueryFn<
  string | FetchArgs,
  unknown,
  FetchBaseQueryError
> = async (args, api, extraOptions) => {
  const path = typeof args === "string" ? args : args.url;
  if (path.startsWith(AUTH_ENDPOINT_PREFIX)) {
    return rawBaseQuery(args, api, extraOptions);
  }

  const pending = pendingRefreshes.get(api.getState);
  if (pending || (!selectAccessToken(stateOf(api)) && selectRefreshToken(stateOf(api)))) {
    const refreshed = await (pending ?? sharedRefresh(api, extraOptions));
    if ("error" in refreshed) {
      return { error: refreshed.error };
    }
  }

  const accessToken = selectAccessToken(stateOf(api));
  const refreshToken = selectRefreshToken(stateOf(api));
  const result = await rawBaseQuery(args, api, extraOptions);
  if (result.error?.status !== 401) {
    return result;
  }
  const currentAccess = selectAccessToken(stateOf(api));
  if (currentAccess && currentAccess !== accessToken) {
    return rawBaseQuery(args, api, extraOptions);
  }
  if (!refreshToken || selectRefreshToken(stateOf(api)) !== refreshToken) {
    return result;
  }
  const refreshed = await sharedRefresh(api, extraOptions);
  return "error" in refreshed ? { error: refreshed.error } : rawBaseQuery(args, api, extraOptions);
};
