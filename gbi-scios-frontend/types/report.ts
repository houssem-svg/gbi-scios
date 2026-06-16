// src/types/report.ts

export interface Report {
  id: number;
  project_id: string;
  generated_by?: string | null;
  report_type: "EXECUTIVE" | "COMPREHENSIVE";
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
  json_payload?: {
    metadata: {
      project_id: string;
      project_name: string;
      report_id: number;
      generated_at: string;
    };
    compliance_summary: {
      total_violations: number;
      resolved_violations: number;
      unresolved_violations: number;
      total_non_compliant_value: number;
      top_violation_categories: Array<Record<string, unknown>>;
    };
    exposure_metrics: {
      total_financial_exposure: number;
      mandatory_list_penalties: number;
      estimated_payroll_leakage: number;
      exposure_percentage_vs_project_budget: number;
    };
    risk_profile: {
      risk_level: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
      critical_flags_count: number;
      top_risk_items: Array<Record<string, unknown>>;
      executive_risk_summary: string;
    };
  } | null;
  file_path?: string | null;
  created_at: string;
  updated_at: string;
}

export interface GenerateReportInput {
  project_id: string;
  report_type?: "EXECUTIVE" | "COMPREHENSIVE";
}

export interface ReportListResponse {
  data: Report[];
  total: number;
}
