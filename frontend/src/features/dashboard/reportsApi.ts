import { baseApi } from "@/shared/api/baseApi";
import type { MyTime, Overview, RetainerReport } from "@/shared/api/types";

export const reportsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getOverview: build.query<Overview, string>({
      query: (period) => ({ url: "/reports/overview/", params: { period } }),
      providesTags: ["Reports"],
    }),
    getRetainerReport: build.query<RetainerReport, string>({
      query: (period) => ({ url: "/reports/retainers/", params: { period } }),
      providesTags: ["Reports"],
    }),
    getMyTime: build.query<MyTime, string>({
      query: (period) => ({ url: "/reports/my-time/", params: { period } }),
      providesTags: ["Reports"],
    }),
  }),
});

export const { useGetOverviewQuery, useGetRetainerReportQuery, useGetMyTimeQuery } = reportsApi;
