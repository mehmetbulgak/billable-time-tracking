import { baseApi } from "@/shared/api/baseApi";
import type { Paginated, Project } from "@/shared/api/types";

export interface ProjectFilters {
  client?: number;
  is_archived?: boolean;
  page_size?: number;
}

export type ProjectInput = Pick<Project, "client" | "name" | "code" | "color" | "is_billable">;

export interface ProjectPatch extends Partial<ProjectInput> {
  id: number;
  is_archived?: boolean;
}

const LIST_TAG = { type: "Projects", id: "LIST" } as const;

export const projectsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    listProjects: build.query<Paginated<Project>, ProjectFilters>({
      query: (params) => ({ url: "/projects/", params: { page_size: 200, ...params } }),
      providesTags: (result) => [
        LIST_TAG,
        ...(result?.results.map((project) => ({ type: "Projects" as const, id: project.id })) ??
          []),
      ],
    }),
    createProject: build.mutation<Project, ProjectInput>({
      query: (body) => ({ url: "/projects/", method: "POST", body }),
      invalidatesTags: [LIST_TAG],
    }),
    updateProject: build.mutation<Project, ProjectPatch>({
      query: ({ id, ...body }) => ({ url: `/projects/${id}/`, method: "PATCH", body }),
      invalidatesTags: (_result, _error, { id }) => [LIST_TAG, { type: "Projects", id }],
    }),
    deleteProject: build.mutation<undefined, number>({
      query: (id) => ({ url: `/projects/${id}/`, method: "DELETE" }),
      invalidatesTags: [LIST_TAG],
    }),
  }),
});

export const {
  useListProjectsQuery,
  useCreateProjectMutation,
  useUpdateProjectMutation,
  useDeleteProjectMutation,
} = projectsApi;
