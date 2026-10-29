import CssBaseline from "@mui/material/CssBaseline";
import { ThemeProvider } from "@mui/material/styles";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { render, type RenderResult } from "@testing-library/react";
import type { ReactElement } from "react";
import { Provider } from "react-redux";
import { MemoryRouter } from "react-router";

import { makeStore, type AppStore, type RootState } from "@/app/store";
import { theme } from "@/app/theme";

interface RenderOptions {
  preloadedState?: Partial<RootState>;
  route?: string;
}

export function renderWithProviders(
  ui: ReactElement,
  { preloadedState, route = "/" }: RenderOptions = {},
): RenderResult & { store: AppStore } {
  const store = makeStore(preloadedState);
  const result = render(
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <LocalizationProvider dateAdapter={AdapterDayjs}>
          <CssBaseline />
          <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
        </LocalizationProvider>
      </ThemeProvider>
    </Provider>,
  );
  return { ...result, store };
}

type Route = (request: Request) => Response | undefined;

export function mockFetch(...routes: Route[]) {
  const calls: Request[] = [];
  const fetchMock = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const request = input instanceof Request ? input : new Request(input, init);
    calls.push(request.clone());
    for (const route of routes) {
      const response = route(request);
      if (response) {
        return Promise.resolve(response);
      }
    }
    if (request.method === "GET" && new URL(request.url).pathname === "/api/v1/auth/csrf/") {
      return json({ csrf_token: "csrf" });
    }
    return Promise.resolve(new Response(JSON.stringify({ detail: "Not found" }), { status: 404 }));
  };
  return { fetchMock, calls };
}

export const json = (body: unknown, status = 200): Response =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

export const route =
  (method: string, pathname: string, respond: (request: Request) => Response): Route =>
  (request) =>
    request.method === method && new URL(request.url).pathname === pathname
      ? respond(request)
      : undefined;
