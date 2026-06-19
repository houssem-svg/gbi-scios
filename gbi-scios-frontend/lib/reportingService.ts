// gbi-scios-frontend/lib/reportingService.ts

import { apiClient, API_BASE_URL } from "./api";
import { GenerateReportInput, Report, ReportListResponse } from "@/types/report";

export const reportingService = {
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
