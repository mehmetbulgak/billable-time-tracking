import { createBrowserRouter, Navigate } from "react-router";

import { LoginPage } from "@/features/auth/LoginPage";
import { RequireAuth } from "@/features/auth/RequireAuth";
import { RequireManager } from "@/features/auth/RequireManager";
import { FullPageLoader } from "@/shared/components/FullPageLoader";

import { AppLayout } from "./AppLayout";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    element: <RequireAuth />,
    hydrateFallbackElement: <FullPageLoader />,
    children: [
      {
        element: <AppLayout />,
        children: [
          {
            index: true,
            lazy: async () => ({
              Component: (await import("@/features/dashboard/DashboardPage")).DashboardPage,
            }),
          },
          {
            path: "timesheet",
            lazy: async () => ({
              Component: (await import("@/features/timeEntries/TimesheetPage")).TimesheetPage,
            }),
          },
          {
            path: "team",
            lazy: async () => ({
              Component: (await import("@/features/team/TeamPage")).TeamPage,
            }),
          },
          {
            element: <RequireManager />,
            children: [
              {
                path: "clients",
                lazy: async () => ({
                  Component: (await import("@/features/clients/ClientsPage")).ClientsPage,
                }),
              },
              {
                path: "clients/:clientId",
                lazy: async () => ({
                  Component: (await import("@/features/clients/ClientDetailPage")).ClientDetailPage,
                }),
              },
              {
                path: "invoices",
                lazy: async () => ({
                  Component: (await import("@/features/invoices/InvoicesPage")).InvoicesPage,
                }),
              },
              {
                path: "invoices/:invoiceId",
                lazy: async () => ({
                  Component: (await import("@/features/invoices/InvoiceDetailPage"))
                    .InvoiceDetailPage,
                }),
              },
            ],
          },
        ],
      },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);
