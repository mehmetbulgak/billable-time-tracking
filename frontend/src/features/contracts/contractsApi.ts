import { baseApi } from "@/shared/api/baseApi";
import type { Contract, Paginated } from "@/shared/api/types";

export type ContractInput = Omit<Contract, "id" | "client_name" | "has_invoices" | "created_at">;

export interface ContractPatch extends Partial<ContractInput> {
  id: number;
}

const LIST_TAG = { type: "Contracts", id: "LIST" } as const;

export const contractsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    listContracts: build.query<Paginated<Contract>, { client?: number }>({
      query: (params) => ({ url: "/contracts/", params: { page_size: 200, ...params } }),
      providesTags: [LIST_TAG],
    }),
    createContract: build.mutation<Contract, ContractInput>({
      query: (body) => ({ url: "/contracts/", method: "POST", body }),
      invalidatesTags: [LIST_TAG, "Reports"],
    }),
    updateContract: build.mutation<Contract, ContractPatch>({
      query: ({ id, ...body }) => ({ url: `/contracts/${id}/`, method: "PATCH", body }),
      invalidatesTags: [LIST_TAG, "Reports"],
    }),
    deleteContract: build.mutation<undefined, number>({
      query: (id) => ({ url: `/contracts/${id}/`, method: "DELETE" }),
      invalidatesTags: [LIST_TAG, "Reports"],
    }),
  }),
});

export const {
  useListContractsQuery,
  useCreateContractMutation,
  useUpdateContractMutation,
  useDeleteContractMutation,
} = contractsApi;
