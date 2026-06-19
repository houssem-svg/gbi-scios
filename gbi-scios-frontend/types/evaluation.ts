/**
 * TypeScript types for the bid evaluation engine.
 *
 * Mirrors the backend Pydantic schemas in:
 *   build-a-production-grade-fastapi-backend/app/schemas/{evaluation,bid}.py
 *
 * All UUID fields arrive as strings (the backend serializes them via
 * field_serializer). All Decimal fields arrive as floats.
 */

/** Backend enum: app/models/bid.py → EvaluationFormula. */
export type EvaluationFormula =
  | "SIXTY_FORTY"
  | "SEVENTY_THIRTY"
  | "FIFTY_FIFTY"
  | "CUSTOM";

/** GET/PUT /api/v1/evaluations/criteria/{project_id} */
export interface EvaluationCriteria {
  id: string;
  project_id: string;
  formula: EvaluationFormula;
  lc_weight: number;
  price_weight: number;
  sme_preference_pct: number;
  tadawul_bonus_pts: number;
  rhq_required: boolean;
  risk_cap_pct: number;
  waiver_cap_pct: number;
  created_at: string;
  updated_at: string;
}

/** PUT /api/v1/evaluations/criteria/{project_id} — all fields optional. */
export interface CriteriaUpdateInput {
  formula?: EvaluationFormula;
  lc_weight?: number;
  price_weight?: number;
  sme_preference_pct?: number;
  tadawul_bonus_pts?: number;
  rhq_required?: boolean;
  risk_cap_pct?: number;
  waiver_cap_pct?: number;
}

/** POST /api/v1/evaluations/bids/{project_id} body. */
export interface BidCreateInput {
  supplier_id: string;
  submitted_price: number;
  local_content_score: number;
  evaluation_formula?: EvaluationFormula;
  custom_lc_weight?: number | null;
  custom_price_weight?: number | null;
}

/** GET /api/v1/evaluations/bids/{project_id} → BidRead[]. */
export interface Bid {
  id: string;
  project_id: string;
  supplier_id: string;
  submitted_price: number;
  local_content_score: number;
  evaluation_formula: EvaluationFormula;
  custom_lc_weight: number | null;
  custom_price_weight: number | null;
  sme_preference_applied: boolean;
  tadawul_bonus_applied: boolean;
  effective_price: number | null;
  final_score: number | null;
  rank: number | null;
  created_at: string;
  updated_at: string;
}

/** Per-bid result inside EvaluationRunResponse.results[]. */
export interface EvaluationResult {
  id: string;
  project_id: string;
  bid_id: string;
  effective_price: number;
  final_score: number;
  rank: number;
  disqualified: boolean;
  disqualification_reason: string | null;
  breakdown_json: string;
  calculated_at: string;
}

/** POST /api/v1/evaluations/run/{project_id} → EvaluationRunResponse. */
export interface EvaluationRunResponse {
  project_id: string;
  results: EvaluationResult[];
  risk_cap_breached: boolean;
  risk_cap_pct: number;
  total_exposure: number;
  project_budget: number;
}

/**
 * Parsed breakdown stored inside EvaluationResult.breakdown_json.
 * Shape matches the dict built by bid_evaluation_service.run_evaluation.
 */
export interface ResultBreakdown {
  bid_id?: string;
  supplier_id?: string;
  formula?: string;
  lc_weight?: string;
  price_weight?: string;
  sme_preference_pct?: string;
  tadawul_bonus_pts?: string;
  rhq_required?: boolean;
  disqualified?: boolean;
  disqualification_reason?: string;
  effective_price?: string;
  lc_score_raw?: string;
  tadawul_bonus_applied?: boolean;
  tadawul_bonus_added?: string;
  price_score?: string;
  weighted_score?: string;
  final_score?: string;
}

/** Human-readable labels for the formula enum. */
export const FORMULA_LABELS: Record<EvaluationFormula, string> = {
  SIXTY_FORTY: "60/40 (Price × 60 + LC × 40)",
  SEVENTY_THIRTY: "70/30 (Price × 30 + LC × 70)",
  FIFTY_FIFTY: "50/50 (Equal weights)",
  CUSTOM: "Custom weights",
};

/** All formula values for <select> options. */
export const ALL_FORMULAS: EvaluationFormula[] = [
  "SIXTY_FORTY",
  "SEVENTY_THIRTY",
  "FIFTY_FIFTY",
  "CUSTOM",
];
