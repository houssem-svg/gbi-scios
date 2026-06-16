// src/lib/reportingService.ts

import { apiClient } from "./api";
import { GenerateReportInput, Report, ReportListResponse } from "@/types/report";

const BASE_URL = "http://127.0.0.1:8000/api/v1";

export const reportingService = {
  async getReportsByProject(projectId: string): Promise<Report[]> {
    const response = await apiClient.get<ReportListResponse | Report[]>(`/reporting/project/${projectId}`);
    return Array.isArray(response) ? response : response.data;
  },

  async generateReport(data: GenerateReportInput): Promise<Report> {
    return apiClient.post<Report>("/reporting/generate", data);
  },

  async downloadReport(reportId: number, filename: string): Promise<void> {
    const token = localStorage.getItem("access_token");
    const headers: HeadersInit = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token.trim()}`;
    }

    const response = await fetch(`${BASE_URL}/reporting/download/${reportId}`, {
      method: "GET",
      headers,
    });

    if (!response.ok) {
      throw new Error(`Failed to download report: ${response.statusText}`);
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename.endsWith('.pdf') ? filename : `${filename}.pdf`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },
};
