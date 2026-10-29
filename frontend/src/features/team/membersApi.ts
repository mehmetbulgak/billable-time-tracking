import { baseApi } from "@/shared/api/baseApi";
import type { Member, Paginated, Role } from "@/shared/api/types";

export interface MemberInput {
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
  password: string;
}

export interface MemberPatch {
  id: number;
  role?: Role;
  is_active?: boolean;
}

export const membersApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    listMembers: build.query<Paginated<Member>, { is_active?: boolean }>({
      query: (params) => ({ url: "/members/", params: { page_size: 200, ...params } }),
      providesTags: ["Members"],
    }),
    createMember: build.mutation<Member, MemberInput>({
      query: (body) => ({ url: "/members/", method: "POST", body }),
      invalidatesTags: ["Members"],
    }),
    updateMember: build.mutation<Member, MemberPatch>({
      query: ({ id, ...body }) => ({ url: `/members/${id}/`, method: "PATCH", body }),
      invalidatesTags: ["Members"],
    }),
  }),
});

export const { useListMembersQuery, useCreateMemberMutation, useUpdateMemberMutation } = membersApi;
