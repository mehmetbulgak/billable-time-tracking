import { baseApi } from "@/shared/api/baseApi";
import type { Client, Paginated } from "@/shared/api/types";

export interface ClientFilters {
  is_archived?: boolean;
  search?: string;
  page_size?: number;
}

export type ClientInput = Pick<
  Client,
  "name" | "contact_name" | "email" | "currency" | "tax_rate" | "payment_terms_days"
>;

export interface ClientPatch extends Partial<ClientInput> {
  id: number;
  is_archived?: boolean;
}

const LIST_TAG = { type: "Clients", id: "LIST" } as const;

export const clientsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    listClients: build.query<Paginated<Client>, ClientFilters>({
      query: (params) => ({ url: "/clients/", params: { page_size: 200, ...params } }),
      providesTags: (result) => [
        LIST_TAG,
        ...(result?.results.map((client) => ({ type: "Clients" as const, id: client.id })) ?? []),
      ],
    }),
    getClient: build.query<Client, number>({
      query: (id) => `/clients/${id}/`,
      providesTags: (_result, _error, id) => [{ type: "Clients", id }],
    }),
    createClient: build.mutation<Client, ClientInput>({
      query: (body) => ({ url: "/clients/", method: "POST", body }),
      invalidatesTags: [LIST_TAG],
    }),
    updateClient: build.mutation<Client, ClientPatch>({
      query: ({ id, ...body }) => ({ url: `/clients/${id}/`, method: "PATCH", body }),
      invalidatesTags: (_result, _error, { id }) => [LIST_TAG, { type: "Clients", id }, "Projects"],
    }),
    deleteClient: build.mutation<undefined, number>({
      query: (id) => ({ url: `/clients/${id}/`, method: "DELETE" }),
      invalidatesTags: [LIST_TAG],
    }),
  }),
});

export const {
  useListClientsQuery,
  useGetClientQuery,
  useCreateClientMutation,
  useUpdateClientMutation,
  useDeleteClientMutation,
} = clientsApi;
