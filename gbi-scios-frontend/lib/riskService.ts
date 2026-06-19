// src/lib/riskService.ts

import { apiClient } from "./api";

export interface RiskLedgerEntry {
  id: string;
  risk_type: string;
  severity_level: string;
  financial_exposure: number;
  recommendation: string;
  created_at: string;
}

export interface RiskDashboard {
  total_exposure: number;
  risk_breakdown: RiskLedgerEntry[];
  executive_summary: string;
  mitigation_actions: string[];
  win_probability: number;
  payroll_leakage: number;
  payroll_recognition_factor: number;
}

export const riskService = {
  /** POST /risk/calculate/{projectId} — compute risk for the project. */
  async calculateRisk(projectId: string): Promise<RiskDashboard> {
    return apiClient.post<RiskDashboard>(`/risk/calculate/${projectId}`, {});
  },

  /** GET /risk/dashboard/{projectId} — same as calculate (read view). */
  async getDashboard(projectId: string): Promise<RiskDashboard> {
    return apiClient.get<RiskDashboard>(`/risk/dashboard/${projectId}`);
  },
};
