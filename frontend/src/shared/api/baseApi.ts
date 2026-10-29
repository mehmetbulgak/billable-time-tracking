import {
  createApi,
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

export const API_URL = import.meta.env.VITE_API_URL ?? "/api/v1";

interface StateWithAuth {
  auth: AuthState;
}

const stateOf = (api: Pick<BaseQueryApi, "getState">): StateWithAuth =>
  api.getState() as StateWithAuth;

const rawBaseQuery = fetchBaseQuery({
  baseUrl: API_URL,
  prepareHeaders: (headers, api) => {
    const token = selectAccessToken(stateOf(api));
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    return headers;
  },
});

let pendingRefresh: Promise<boolean> | null = null;

const AUTH_ENDPOINT_PREFIX = "/auth/token/";

const isAuthRequest = (args: string | FetchArgs): boolean =>
  (typeof args === "string" ? args : args.url).startsWith(AUTH_ENDPOINT_PREFIX);

async function refreshTokens(api: BaseQueryApi, extraOptions: object): Promise<boolean> {
  const refreshToken = selectRefreshToken(stateOf(api));
  if (!refreshToken) {
    api.dispatch(loggedOut());
    return false;
  }
  const response = await rawBaseQuery(
    { url: `${AUTH_ENDPOINT_PREFIX}refresh/`, method: "POST", body: { refresh: refreshToken } },
    api,
    extraOptions,
  );
  if (isTokenPair(response.data)) {
    api.dispatch(tokensReceived(response.data));
    return true;
  }
  api.dispatch(loggedOut());
  return false;
}

function sharedRefresh(api: BaseQueryApi, extraOptions: object): Promise<boolean> {
  pendingRefresh ??= refreshTokens(api, extraOptions).finally(() => {
    pendingRefresh = null;
  });
  return pendingRefresh;
}

const hasOnlyRefreshToken = (state: StateWithAuth): boolean =>
  selectAccessToken(state) === null && selectRefreshToken(state) !== null;

const baseQueryWithReauth: BaseQueryFn<string | FetchArgs, unknown, FetchBaseQueryError> = async (
  args,
  api,
  extraOptions,
) => {
  if (isAuthRequest(args)) {
    return rawBaseQuery(args, api, extraOptions);
  }
  if (pendingRefresh) {
    await pendingRefresh;
  } else if (hasOnlyRefreshToken(stateOf(api))) {
    await sharedRefresh(api, extraOptions);
  }
  const result = await rawBaseQuery(args, api, extraOptions);
  if (result.error?.status !== 401) {
    return result;
  }
  const refreshed = await sharedRefresh(api, extraOptions);
  return refreshed ? rawBaseQuery(args, api, extraOptions) : result;
};

export const baseApi = createApi({
  reducerPath: "api",
  baseQuery: baseQueryWithReauth,
  tagTypes: [
    "CurrentUser",
    "Organization",
    "Members",
    "Clients",
    "Projects",
    "Contracts",
    "TimeEntries",
    "CurrentTimer",
    "ActiveTimers",
    "Invoices",
    "Reports",
  ],
  endpoints: () => ({}),
});
