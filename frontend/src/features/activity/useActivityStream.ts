import { useEffect, useState } from "react";

import { useAppDispatch, useAppSelector, useAppStore } from "@/app/hooks";
import { authApi } from "@/features/auth/authApi";
import { selectAccessToken, selectHasSession } from "@/features/auth/authSlice";
import { baseApi } from "@/shared/api/baseApi";

import { createActivityConnection, type ConnectionStatus } from "./activityConnection";
import { applyActivityEvent } from "./applyActivityEvent";

export type { ConnectionStatus } from "./activityConnection";

export function useActivityStream(): ConnectionStatus {
  const dispatch = useAppDispatch();
  const store = useAppStore();
  const hasSession = useAppSelector(selectHasSession);
  const [status, setStatus] = useState<ConnectionStatus>("connecting");

  useEffect(() => {
    if (!hasSession) {
      return undefined;
    }

    return createActivityConnection({
      getToken: () => selectAccessToken(store.getState()),
      onStatus: setStatus,
      onEvent: (event) => {
        dispatch(applyActivityEvent(event));
      },
      onReconnect: () => {
        dispatch(
          baseApi.util.invalidateTags([
            "ActiveTimers",
            "CurrentTimer",
            "TimeEntries",
            "Invoices",
            "Reports",
          ]),
        );
      },
      refreshSession: () => {
        void dispatch(
          authApi.endpoints.getCurrentUser.initiate(undefined, {
            forceRefetch: true,
            subscribe: false,
          }),
        );
      },
    });
  }, [dispatch, hasSession, store]);

  return status;
}
