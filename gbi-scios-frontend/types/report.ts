// src/types/report.ts

/**
 * Mirrors backend `ReportRead` (app/schemas/reporting.py):
 * { id (int), project_id, generated_by, report_type, status, file_path, json_payload, created_at }
 *
 * `json_payload` is intentionally a free-form object — the backend builds it
 * dynamically from compliance/exposure/risk metrics and its exact shape can
 * drift; we type only the keys the UI actually reads.
 */
export interface ReportJsonPayload {
  metadata?: {
    project_id?: string;
    project_name?: string;
    report_id?: number;
    generated_at?: string;
  };
  compliance_summary?: {
    total_violations?: number;
    resolved_violations?: number;
    unresolved_violations?: number;
    total_non_compliant_value?: number;
    top_violation_categories?: Array<Record<string, unknown>>;
  };
  exposure_metrics?: {
    total_financial_exposure?: number;
    mandatory_list_penalties?: number;
    estimated_payroll_leakage?: number;
    exposure_percentage_vs_project_budget?: number;
  };
  risk_profile?: {
    risk_level?: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
    critical_flags_count?: number;
    top_risk_items?: Array<Record<string, unknown>>;
    executive_risk_summary?: string;
  };
}

export interface Report {
  id: number;
  project_id: string;
  generated_by?: string | null;
  report_type: "EXECUTIVE" | "COMPREHENSIVE";
  status: "PENDING" | "COMPLETED" | "FAILED";
  file_path?: string | null;
  json_payload?: ReportJsonPayload | null;
  created_at: string;
}

export interface GenerateReportInput {
  project_id: string;
  report_type?: "EXECUTIVE" | "COMPREHENSIVE";
}

export interface ReportListResponse {
  reports: Report[];
  total: number;
}
