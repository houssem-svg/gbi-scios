// src/types/compliance.ts

export type ComplianceFlagStatus = "open" | "waived" | "resolved";
export type ViolationType =
  | "imported_mandatory_item"
  | "local_content_quota_unmet"
  | "non_rhq_supplier"
  | "payroll_leakage"
  | "risk_cap_breach";

export interface ComplianceFlag {
  id: string;
  project_id: string;
  boq_item_id: string;
  mandatory_item_id: string;
  violation_type: ViolationType;
  penalty_percentage: number;
  exposure_amount: number;
  status: ComplianceFlagStatus;
  created_at: string;
  updated_at?: string | null;
  waived_by?: string | null;
  waived_at?: string | null;
  waiver_reason?: string | null;
  waiver_strategy_id?: string | null;
  boq_item_code?: string | null;
  boq_description?: string | null;
  mandatory_product_name?: string | null;
}

export interface ComplianceScanResult {
  total_scanned_items: number;
  matched_violations: number;
  total_exposure: number;
  compliance_status: string;
  flags: ComplianceFlag[];
}

export interface FlagStatusUpdate {
  status: ComplianceFlagStatus;
  waiver_reason: string;
  waiver_strategy_id?: string;
}
