import { createListenerMiddleware } from "@reduxjs/toolkit";

import { loggedOut, tokensReceived } from "@/features/auth/authSlice";
import { tokenStorage } from "@/features/auth/tokenStorage";
import { baseApi } from "@/shared/api/baseApi";

export const listenerMiddleware = createListenerMiddleware();

listenerMiddleware.startListening({
  actionCreator: tokensReceived,
  effect: (action) => {
    tokenStorage.write(action.payload.refresh);
  },
});

listenerMiddleware.startListening({
  actionCreator: loggedOut,
  effect: (_action, api) => {
    tokenStorage.clear();
    api.dispatch(baseApi.util.resetApiState());
  },
});
