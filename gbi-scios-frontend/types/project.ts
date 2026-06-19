// types/project.ts

/**
 * Mirrors backend `ProjectRead` (app/schemas/project.py):
 * { id, project_name, client_name, sector, status, created_at, owner_id }
 *
 * The frontend keeps `name`/`client` aliases (mapped in projectService) so
 * existing UI components keep working without a wide refactor.
 *
 * risk_level / compliance_score are intentionally removed — they do NOT exist
 * on the backend ProjectRead (audit finding FE-9).
 */

export type ProjectStatus =
  | "Planning"
  | "Active"
  | "On Hold"
  | "Completed"
  | "Cancelled";

export interface Project {
  id: string;
  // Frontend-friendly aliases (mapped from project_name / client_name).
  name: string;
  client: string;
  sector: string;
  status: ProjectStatus;
  created_at: string;
  owner_id: string;
}

export interface ProjectCreateInput {
  project_name: string;
  client_name: string;
  sector?: string;
  status?: ProjectStatus;
}

export interface ProjectUpdateInput {
  project_name?: string;
  client_name?: string;
  sector?: string;
  status?: ProjectStatus;
}
