import CssBaseline from "@mui/material/CssBaseline";
import { ThemeProvider } from "@mui/material/styles";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { Provider } from "react-redux";
import { RouterProvider } from "react-router";

import { Notifier } from "@/shared/feedback/Notifier";

import { router } from "./router";
import type { AppStore } from "./store";
import { theme } from "./theme";

export function App({ store }: { store: AppStore }) {
  return (
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale="en-gb">
          <CssBaseline />
          <RouterProvider router={router} />
          <Notifier />
        </LocalizationProvider>
      </ThemeProvider>
    </Provider>
  );
}
