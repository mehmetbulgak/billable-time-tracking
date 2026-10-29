import type { CurrentUser } from "@/shared/api/types";

import { useGetCurrentUserQuery } from "./authApi";

export function useCurrentUser(): CurrentUser {
  const { data } = useGetCurrentUserQuery();
  if (!data) {
    throw new Error("useCurrentUser can only be used inside an authenticated route.");
  }
  return data;
}
