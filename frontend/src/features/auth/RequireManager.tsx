import { Navigate, Outlet } from "react-router";

import { useCurrentUser } from "./useCurrentUser";

export function RequireManager() {
  const user = useCurrentUser();
  return user.is_manager ? <Outlet /> : <Navigate to="/" replace />;
}
