import { createSlice, nanoid, type PayloadAction } from "@reduxjs/toolkit";

export type NotificationSeverity = "success" | "info" | "warning" | "error";

export interface Notification {
  id: string;
  message: string;
  severity: NotificationSeverity;
}

interface NotificationsState {
  queue: Notification[];
}

const initialState: NotificationsState = { queue: [] };

export const notificationsSlice = createSlice({
  name: "notifications",
  initialState,
  reducers: {
    notified: {
      reducer(state, action: PayloadAction<Notification>) {
        state.queue.push(action.payload);
      },
      prepare(message: string, severity: NotificationSeverity = "success") {
        return { payload: { id: nanoid(), message, severity } };
      },
    },
    dismissed(state, action: PayloadAction<string>) {
      state.queue = state.queue.filter((notification) => notification.id !== action.payload);
    },
  },
  selectors: {
    selectCurrentNotification: (state) => state.queue[0] ?? null,
  },
});

export const { notified, dismissed } = notificationsSlice.actions;
export const { selectCurrentNotification } = notificationsSlice.selectors;
