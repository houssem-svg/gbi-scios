// src/lib/complianceService.ts

import { apiClient } from "./api";
import type {
  ComplianceFlag,
  ComplianceScanResult,
  FlagStatusUpdate,
} from "@/types/compliance";

export const complianceService = {
  /** POST /compliance/scan/{projectId} — run the compliance scan. */
  async scanProject(projectId: string): Promise<ComplianceScanResult> {
    return apiClient.post<ComplianceScanResult>(
      `/compliance/scan/${projectId}`,
      {},
    );
  },

  /** GET /compliance/project/{projectId} — list flags with skip/limit. */
  async listFlags(
    projectId: string,
    options?: { skip?: number; limit?: number },
  ): Promise<ComplianceFlag[]> {
    const skip = options?.skip ?? 0;
    const limit = options?.limit ?? 200;
    const res = await apiClient.get<ComplianceFlag[]>(
      `/compliance/project/${projectId}`,
      { params: { skip: String(skip), limit: String(limit) } },
    );
    return Array.isArray(res) ? res : [];
  },

  /** PATCH /compliance/flags/{flagId} — waive or resolve a flag. */
  async updateFlagStatus(
    flagId: string,
    payload: FlagStatusUpdate,
  ): Promise<ComplianceFlag> {
    return apiClient.patch<ComplianceFlag>(`/compliance/flags/${flagId}`, payload);
  },
};
