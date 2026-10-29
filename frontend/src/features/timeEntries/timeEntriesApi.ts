import { baseApi } from "@/shared/api/baseApi";
import type { Paginated, TimeEntry } from "@/shared/api/types";

export interface TimeEntryFilters {
  started_after?: string;
  started_before?: string;
  user?: number;
  project?: number;
  client?: number;
  is_billable?: boolean;
  is_invoiced?: boolean;
  page?: number;
  page_size?: number;
  ordering?: string;
}

export interface TimeEntryInput {
  project: number;
  description: string;
  started_at: string;
  ended_at: string;
  is_billable?: boolean | null;
}

export interface TimeEntryPatch extends Partial<TimeEntryInput> {
  id: number;
}

export interface TimerStartInput {
  project: number;
  description: string;
}

const LIST_TAG = { type: "TimeEntries", id: "LIST" } as const;
const TIME_CHANGES = [LIST_TAG, "CurrentTimer", "ActiveTimers", "Reports"] as const;

export const timeEntriesApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    listTimeEntries: build.query<Paginated<TimeEntry>, TimeEntryFilters>({
      query: (params) => ({ url: "/time-entries/", params }),
      providesTags: (result) => [
        LIST_TAG,
        ...(result?.results.map((entry) => ({ type: "TimeEntries" as const, id: entry.id })) ?? []),
      ],
    }),
    getCurrentTimer: build.query<TimeEntry | null, void>({
      query: () => "/time-entries/current/",
      transformResponse: (response: TimeEntry | null) => response ?? null,
      providesTags: ["CurrentTimer"],
    }),
    getActiveTimers: build.query<TimeEntry[], void>({
      query: () => "/time-entries/active/",
      providesTags: ["ActiveTimers"],
    }),
    startTimer: build.mutation<TimeEntry, TimerStartInput>({
      query: (body) => ({ url: "/time-entries/start/", method: "POST", body }),
      async onQueryStarted(_input, { dispatch, queryFulfilled }) {
        try {
          const { data } = await queryFulfilled;
          void dispatch(timeEntriesApi.util.upsertQueryData("getCurrentTimer", undefined, data));
        } catch {
          return;
        }
      },
      invalidatesTags: [LIST_TAG, "ActiveTimers", "Reports"],
    }),
    stopTimer: build.mutation<TimeEntry, void>({
      query: () => ({ url: "/time-entries/stop/", method: "POST" }),
      async onQueryStarted(_input, { dispatch, queryFulfilled }) {
        try {
          await queryFulfilled;
          void dispatch(timeEntriesApi.util.upsertQueryData("getCurrentTimer", undefined, null));
        } catch {
          return;
        }
      },
      invalidatesTags: [LIST_TAG, "ActiveTimers", "Reports"],
    }),
    createTimeEntry: build.mutation<TimeEntry, TimeEntryInput>({
      query: (body) => ({ url: "/time-entries/", method: "POST", body }),
      invalidatesTags: [...TIME_CHANGES],
    }),
    updateTimeEntry: build.mutation<TimeEntry, TimeEntryPatch>({
      query: ({ id, ...body }) => ({ url: `/time-entries/${id}/`, method: "PATCH", body }),
      invalidatesTags: [...TIME_CHANGES],
    }),
    deleteTimeEntry: build.mutation<undefined, number>({
      query: (id) => ({ url: `/time-entries/${id}/`, method: "DELETE" }),
      invalidatesTags: [...TIME_CHANGES],
    }),
  }),
});

export const {
  useListTimeEntriesQuery,
  useGetCurrentTimerQuery,
  useGetActiveTimersQuery,
  useStartTimerMutation,
  useStopTimerMutation,
  useCreateTimeEntryMutation,
  useUpdateTimeEntryMutation,
  useDeleteTimeEntryMutation,
} = timeEntriesApi;
