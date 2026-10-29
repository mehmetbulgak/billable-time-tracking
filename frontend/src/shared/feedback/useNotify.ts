import { useMemo } from "react";

import { useAppDispatch } from "@/app/hooks";
import { getErrorMessage } from "@/shared/api/errors";

import { notified } from "./notificationsSlice";

export interface Notify {
  success: (message: string) => void;
  info: (message: string) => void;
  error: (error: unknown) => void;
}

export function useNotify(): Notify {
  const dispatch = useAppDispatch();
  return useMemo(
    () => ({
      success: (message) => dispatch(notified(message, "success")),
      info: (message) => dispatch(notified(message, "info")),
      error: (error) => dispatch(notified(getErrorMessage(error), "error")),
    }),
    [dispatch],
  );
}
