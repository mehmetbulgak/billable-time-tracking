import { Navigate, Outlet, useLocation } from "react-router";

import { useAppSelector } from "@/app/hooks";
import { ErrorState } from "@/shared/components/ErrorState";
import { FullPageLoader } from "@/shared/components/FullPageLoader";

import { useGetCurrentUserQuery } from "./authApi";
import { selectHasSession } from "./authSlice";
import { DemoSignIn } from "./DemoSignIn";

export function RequireAuth() {
  const hasSession = useAppSelector(selectHasSession);
  const location = useLocation();
  const { data, error, isLoading, refetch } = useGetCurrentUserQuery(undefined, {
    skip: !hasSession,
  });

  if (!hasSession) {
    if (import.meta.env.VITE_DEMO_MODE === "true") {
      return <DemoSignIn />;
    }
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  if (isLoading) {
    return <FullPageLoader />;
  }
  if (error || !data) {
    return <ErrorState error={error} onRetry={() => void refetch()} fullPage />;
  }
  return <Outlet />;
}
