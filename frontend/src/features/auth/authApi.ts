import { baseApi } from "@/shared/api/baseApi";
import type { CurrentUser, TokenPair } from "@/shared/api/types";

import { tokensReceived } from "./authSlice";

export interface Credentials {
  email: string;
  password: string;
}

export type ProfileInput = Pick<CurrentUser, "first_name" | "last_name">;

export const authApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    login: build.mutation<TokenPair, Credentials>({
      query: (credentials) => ({ url: "/auth/token/", method: "POST", body: credentials }),
      async onQueryStarted(_credentials, { dispatch, queryFulfilled }) {
        try {
          const { data } = await queryFulfilled;
          dispatch(tokensReceived(data));
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

export const { useLoginMutation, useGetCurrentUserQuery, useUpdateProfileMutation } = authApi;
