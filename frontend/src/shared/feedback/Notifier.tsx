import Alert from "@mui/material/Alert";
import Snackbar from "@mui/material/Snackbar";

import { useAppDispatch, useAppSelector } from "@/app/hooks";

import { dismissed, selectCurrentNotification } from "./notificationsSlice";

const AUTO_HIDE_MS = 4000;

export function Notifier() {
  const dispatch = useAppDispatch();
  const notification = useAppSelector(selectCurrentNotification);

  const close = () => {
    if (notification) {
      dispatch(dismissed(notification.id));
    }
  };

  return (
    <Snackbar
      key={notification?.id}
      open={notification !== null}
      autoHideDuration={AUTO_HIDE_MS}
      onClose={(_event, reason) => {
        if (reason !== "clickaway") {
          close();
        }
      }}
      anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
    >
      <Alert severity={notification?.severity ?? "info"} variant="filled" onClose={close}>
        {notification?.message}
      </Alert>
    </Snackbar>
  );
}
