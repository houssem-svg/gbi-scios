// src/types/dashboard.ts

/**
 * Mirrors backend `DashboardSummaryResponse` (app/schemas/dashboard.py):
 *
 * {
 *   total_projects: int,
 *   total_budget_managed: float,
 *   total_financial_exposure: float,
 *   overall_compliance_score: float,
 *   compliance_breakdown: { open_flags, resolved_flags, waived_flags, total_flags },
 *   top_risk_projects: [{ project_id, project_name, project_exposure, flag_count }]
 * }
 */

export interface ComplianceBreakdown {
  open_flags: number;
  resolved_flags: number;
  waived_flags: number;
  total_flags: number;
}

export interface TopRiskProject {
  project_id: string;
  project_name: string;
  project_exposure: number;
  flag_count: number;
}

export interface DashboardSummary {
  total_projects: number;
  total_budget_managed: number;
  total_financial_exposure: number;
  overall_compliance_score: number;
  compliance_breakdown: ComplianceBreakdown;
  top_risk_projects: TopRiskProject[];
}
