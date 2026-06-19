// src/lib/dashboardService.ts

import { apiClient } from "./api";
import { DashboardSummary } from "@/types/dashboard";

export const dashboardService = {
  /**
   * GET /dashboard/summary → returns the raw backend DashboardSummaryResponse
   * with no field remapping. The DashboardSummary type is a 1:1 match.
   */
  async getSummary(): Promise<DashboardSummary> {
    return apiClient.get<DashboardSummary>("/dashboard/summary");
  },
};
