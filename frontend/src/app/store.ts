import {
  combineSlices,
  configureStore,
  type ThunkAction,
  type UnknownAction,
} from "@reduxjs/toolkit";

import { authSlice } from "@/features/auth/authSlice";
import { baseApi } from "@/shared/api/baseApi";
import { notificationsSlice } from "@/shared/feedback/notificationsSlice";

import { listenerMiddleware } from "./listeners";

export const rootReducer = combineSlices(authSlice, notificationsSlice, baseApi);

export type RootState = ReturnType<typeof rootReducer>;

export const makeStore = (preloadedState?: Partial<RootState>) =>
  configureStore({
    reducer: rootReducer,
    preloadedState,
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().prepend(listenerMiddleware.middleware).concat(baseApi.middleware),
  });

export type AppStore = ReturnType<typeof makeStore>;
export type AppDispatch = AppStore["dispatch"];
export type AppThunk<ReturnType = void> = ThunkAction<
  ReturnType,
  RootState,
  unknown,
  UnknownAction
>;
