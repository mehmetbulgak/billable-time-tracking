import { createListenerMiddleware } from "@reduxjs/toolkit";

import { loggedOut, tokensReceived } from "@/features/auth/authSlice";
import { sessionPersistence } from "@/features/auth/sessionPersistence";
import { baseApi } from "@/shared/api/baseApi";

export const listenerMiddleware = createListenerMiddleware();

listenerMiddleware.startListening({
  actionCreator: tokensReceived,
  effect: () => {
    sessionPersistence.write();
  },
});

listenerMiddleware.startListening({
  actionCreator: loggedOut,
  effect: (_action, api) => {
    sessionPersistence.clear();
    api.dispatch(baseApi.util.resetApiState());
  },
});
