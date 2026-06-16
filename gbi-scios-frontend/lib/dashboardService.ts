// src/lib/dashboardService.ts

import { apiClient } from "./api";
import { DashboardSummary } from "@/types/dashboard";

export const dashboardService = {
  async getSummary(): Promise<DashboardSummary> {
    return apiClient.get<DashboardSummary>("/dashboard/summary");
  },
};