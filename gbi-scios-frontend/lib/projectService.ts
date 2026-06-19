// lib/projectService.ts

import { apiClient } from "./api";
import { Project, ProjectCreateInput, ProjectUpdateInput, ProjectStatus } from "@/types/project";

/**
 * Backend `ProjectRead` raw shape — used as the source of truth for mapping.
 * Defined here so the cast is narrow and explicit instead of `any`.
 */
interface BackendProjectRead {
  id: string;
  project_name: string;
  client_name: string;
  sector?: string;
  status?: string;
  created_at?: string;
  owner_id?: string;
}

const VALID_STATUSES: ProjectStatus[] = [
  "Planning",
  "Active",
  "On Hold",
  "Completed",
  "Cancelled",
];

function coerceStatus(value: unknown): ProjectStatus {
  return VALID_STATUSES.includes(value as ProjectStatus)
    ? (value as ProjectStatus)
    : "Planning";
}

const mapBackendToFrontend = (backendProject: BackendProjectRead): Project => ({
  id: backendProject.id,
  name: backendProject.project_name ?? "",
  client: backendProject.client_name ?? "",
  sector: backendProject.sector ?? "",
  status: coerceStatus(backendProject.status),
  created_at: backendProject.created_at ?? new Date().toISOString(),
  owner_id: backendProject.owner_id ?? "",
});

export const projectService = {
  async getAllProjects(): Promise<Project[]> {
    const response = await apiClient.get<BackendProjectRead[]>("/projects");
    return Array.isArray(response) ? response.map(mapBackendToFrontend) : [];
  },

  async getProjectById(id: string): Promise<Project> {
    const response = await apiClient.get<BackendProjectRead>(`/projects/${id}`);
    return mapBackendToFrontend(response);
  },

  async createProject(data: ProjectCreateInput): Promise<Project> {
    const backendPayload: ProjectCreateInput = {
      project_name: data.project_name,
      client_name: data.client_name,
      sector: data.sector?.trim() ? data.sector : "General",
      status: data.status ?? "Planning",
    };
    const response = await apiClient.post<BackendProjectRead>("/projects", backendPayload);
    return mapBackendToFrontend(response);
  },

  /**
   * FE-10/FE-11: send `sector` and `status` (not just project_name/client_name)
   * when present in the input. Without this the user's status edits were
   * silently dropped.
   */
  async updateProject(id: string, data: ProjectUpdateInput): Promise<Project> {
    const backendPayload: ProjectUpdateInput = {};
    if (data.project_name !== undefined) backendPayload.project_name = data.project_name;
    if (data.client_name !== undefined) backendPayload.client_name = data.client_name;
    if (data.sector !== undefined) backendPayload.sector = data.sector;
    if (data.status !== undefined) backendPayload.status = data.status;

    const response = await apiClient.put<BackendProjectRead>(`/projects/${id}`, backendPayload);
    return mapBackendToFrontend(response);
  },

  async deleteProject(id: string): Promise<void> {
    await apiClient.delete<void>(`/projects/${id}`);
  },
};
