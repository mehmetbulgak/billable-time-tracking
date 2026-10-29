import type { AppThunk } from "@/app/store";
import { loggedOut } from "@/features/auth/authSlice";
import { authApi } from "@/features/auth/authApi";
import { timeEntriesApi } from "@/features/timeEntries/timeEntriesApi";
import { baseApi } from "@/shared/api/baseApi";

import type { ActivityEvent } from "./activityEvents";
import { mergeActiveTimer } from "./activeTimers";

const TIME_ENTRY_LIST = { type: "TimeEntries", id: "LIST" } as const;

export const applyActivityEvent =
  (event: ActivityEvent): AppThunk =>
  (dispatch, getState) => {
    const currentUserId = authApi.endpoints.getCurrentUser.select()(getState()).data?.id;
    const ownTimerTags = (userId: number) =>
      userId === currentUserId ? ["CurrentTimer" as const] : [];

    switch (event.event) {
      case "session.revoked":
        dispatch(loggedOut());
        return;
      case "activity.changed":
        dispatch(baseApi.util.invalidateTags(["ActiveTimers", "Reports"]));
        return;
      case "timer.started":
      case "timer.stopped": {
        const { entry } = event.payload;
        dispatch(
          timeEntriesApi.util.updateQueryData("getActiveTimers", undefined, (timers) =>
            mergeActiveTimer(timers, entry),
          ),
        );
        dispatch(
          baseApi.util.invalidateTags([TIME_ENTRY_LIST, "Reports", ...ownTimerTags(entry.user.id)]),
        );
        return;
      }
      case "entry.changed":
        dispatch(
          baseApi.util.invalidateTags([
            TIME_ENTRY_LIST,
            "ActiveTimers",
            "Reports",
            ...ownTimerTags(event.payload.entry.user.id),
          ]),
        );
        return;
      case "entry.deleted":
        dispatch(
          baseApi.util.invalidateTags([
            TIME_ENTRY_LIST,
            "ActiveTimers",
            "Reports",
            ...ownTimerTags(event.payload.user_id),
          ]),
        );
        return;
      case "invoice.changed":
        dispatch(
          baseApi.util.invalidateTags([
            { type: "Invoices", id: "LIST" },
            { type: "Invoices", id: event.payload.invoice_id },
            TIME_ENTRY_LIST,
            "Reports",
          ]),
        );
        return;
      case "pong":
        return;
    }
  };
