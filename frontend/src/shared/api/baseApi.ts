import { createApi } from "@reduxjs/toolkit/query/react";

import { authenticatedQuery } from "./authenticatedQuery";

export const baseApi = createApi({
  reducerPath: "api",
  baseQuery: authenticatedQuery,
  tagTypes: [
    "CurrentUser",
    "Organization",
    "Members",
    "Clients",
    "Projects",
    "Contracts",
    "TimeEntries",
    "CurrentTimer",
    "ActiveTimers",
    "Invoices",
    "Reports",
  ],
  endpoints: () => ({}),
});
