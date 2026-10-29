import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

import type { TokenPair } from "@/shared/api/types";

import { tokenStorage } from "./tokenStorage";

export interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
}

const initialState = (): AuthState => ({
  accessToken: null,
  refreshToken: tokenStorage.read(),
});

export const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    tokensReceived(state, action: PayloadAction<TokenPair>) {
      state.accessToken = action.payload.access;
      state.refreshToken = action.payload.refresh;
    },
    loggedOut(state) {
      state.accessToken = null;
      state.refreshToken = null;
    },
  },
  selectors: {
    selectAccessToken: (state) => state.accessToken,
    selectRefreshToken: (state) => state.refreshToken,
    selectHasSession: (state) => state.refreshToken !== null,
  },
});

export const { tokensReceived, loggedOut } = authSlice.actions;
export const { selectAccessToken, selectRefreshToken, selectHasSession } = authSlice.selectors;
