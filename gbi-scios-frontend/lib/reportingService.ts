// src/lib/reportingService.ts

import { apiClient, API_BASE_URL } from "./api";
import { GenerateReportInput, Report, ReportListResponse } from "@/types/report";

export const reportingService = {
  /**
   * GET /reporting/project/{projectId}?skip=&limit= → Report[] (or
   * { reports: Report[], total: number }).
   *
   * Audit item C-1/P-18: pass skip/limit. The backend may not honor them
   * yet; callers should still handle a full-list response.
   */
  async getReportsByProject(
    projectId: string,
    options?: { skip?: number; limit?: number },
  ): Promise<Report[]> {
    const skip = options?.skip ?? 0;
    const limit = options?.limit ?? 20;
    const response = await apiClient.get<ReportListResponse | Report[]>(
      `/reporting/project/${projectId}`,
      {
        params: {
          skip: String(skip),
          limit: String(limit),
        },
      },
    );
    if (Array.isArray(response)) return response;
    // Backend returns { reports: Report[], total: number }
    return (response as ReportListResponse)?.reports ?? (response as { data?: Report[] })?.data ?? [];
  },

  async generateReport(data: GenerateReportInput): Promise<Report> {
    return apiClient.post<Report>("/reporting/generate", data);
  },

  async downloadReport(reportId: number, filename: string): Promise<void> {
    const token =
      typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token.trim()}`;
    }

    const response = await fetch(`${API_BASE_URL}/reporting/download/${reportId}`, {
      method: "GET",
      headers,
    });

    // FE-6: central 401 handling — re-use the same redirect behavior even
    // though we bypass apiClient for the blob download.
    if (response.status === 401) {
      try {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        document.cookie =
          "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax";
      } catch {
        // ignore
      }
      window.location.href = "/login";
      throw new Error("Session expired. Please sign in again.");
    }

    if (!response.ok) {
      throw new Error(`Failed to download report: ${response.statusText}`);
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename.endsWith(".pdf") ? filename : `${filename}.pdf`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },
};
