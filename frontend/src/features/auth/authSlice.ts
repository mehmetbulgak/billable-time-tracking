import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

import type { AccessSession } from "@/shared/api/types";

import { sessionPersistence } from "./sessionPersistence";

export interface AuthState {
  accessToken: string | null;
  csrfToken: string | null;
  hasSession: boolean;
  sessionVersion: number;
}

const initialState = (): AuthState => ({
  accessToken: null,
  csrfToken: null,
  hasSession: sessionPersistence.read(),
  sessionVersion: 0,
});

export const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    tokensReceived(state, action: PayloadAction<AccessSession>) {
      state.accessToken = action.payload.access;
      state.csrfToken = action.payload.csrf_token;
      state.hasSession = true;
      state.sessionVersion += 1;
    },
    csrfReceived(state, action: PayloadAction<string>) {
      state.csrfToken = action.payload;
    },
    loggedOut(state) {
      state.accessToken = null;
      state.csrfToken = null;
      state.hasSession = false;
      state.sessionVersion += 1;
    },
  },
  selectors: {
    selectAccessToken: (state) => state.accessToken,
    selectHasSession: (state) => state.hasSession,
  },
});

export const { tokensReceived, csrfReceived, loggedOut } = authSlice.actions;
export const { selectAccessToken, selectHasSession } = authSlice.selectors;
