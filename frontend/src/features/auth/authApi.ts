import { baseApi } from "@/shared/api/baseApi";
import type { CurrentUser, AccessSession } from "@/shared/api/types";

import { loggedOut, tokensReceived, type AuthState } from "./authSlice";

export interface Credentials {
  email: string;
  password: string;
}

export type ProfileInput = Pick<CurrentUser, "first_name" | "last_name">;

export const authApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    login: build.mutation<AccessSession, Credentials>({
      query: (credentials) => ({ url: "/auth/token/", method: "POST", body: credentials }),
      async onQueryStarted(_credentials, lifecycle) {
        const { dispatch, queryFulfilled } = lifecycle;
        const version = (lifecycle.getState() as unknown as { auth: AuthState }).auth
          .sessionVersion;
        try {
          const { data } = await queryFulfilled;
          if (
            (lifecycle.getState() as unknown as { auth: AuthState }).auth.sessionVersion === version
          ) {
            dispatch(tokensReceived(data));
          }
        } catch {
          return;
        }
      },
    }),
    logout: build.mutation<void, void>({
      query: () => ({ url: "/auth/logout/", method: "POST", body: {} }),
      async onQueryStarted(_arg, { dispatch, queryFulfilled }) {
        try {
          await queryFulfilled;
          dispatch(loggedOut());
        } catch {
          return;
        }
      },
    }),
    getCurrentUser: build.query<CurrentUser, void>({
      query: () => "/auth/me/",
      providesTags: ["CurrentUser"],
    }),
    updateProfile: build.mutation<CurrentUser, ProfileInput>({
      query: (body) => ({ url: "/auth/me/", method: "PATCH", body }),
      invalidatesTags: ["CurrentUser", "Members"],
    }),
  }),
});

export const {
  useLoginMutation,
  useLogoutMutation,
  useGetCurrentUserQuery,
  useUpdateProfileMutation,
} = authApi;
