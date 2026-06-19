"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Scale,
  Loader2,
  Plus,
  Play,
  Save,
  AlertTriangle,
  CheckCircle2,
  Trophy,
  Ban,
} from "lucide-react";
import { projectService } from "@/lib/projectService";
import { evaluationService } from "@/lib/evaluationService";
import { Project } from "@/types/project";
import {
  ALL_FORMULAS,
  FORMULA_LABELS,
  type Bid,
  type BidCreateInput,
  type EvaluationCriteria,
  type EvaluationFormula,
  type EvaluationRunResponse,
  type ResultBreakdown,
} from "@/types/evaluation";

// ─── Helpers ─────────────────────────────────────────────────────────

function formatSAR(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "SAR",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatScore(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return value.toFixed(2);
}

function shortId(id: string | undefined): string {
  if (!id) return "—";
  return id.substring(0, 8);
}

function parseBreakdown(json: string): ResultBreakdown | null {
  try {
    return JSON.parse(json) as ResultBreakdown;
  } catch {
    return null;
  }
}

// ─── Page ────────────────────────────────────────────────────────────

export default function BidEvaluationPage() {
  // Project selection
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [loadingProjects, setLoadingProjects] = useState(true);

  // Criteria
  const [criteria, setCriteria] = useState<EvaluationCriteria | null>(null);
  const [criteriaLoading, setCriteriaLoading] = useState(false);
  const [criteriaSaving, setCriteriaSaving] = useState(false);
  const [criteriaError, setCriteriaError] = useState<string | null>(null);

  // Bids
  const [bids, setBids] = useState<Bid[]>([]);
  const [bidsLoading, setBidsLoading] = useState(false);

  // Add-bid inline form
  const [showBidForm, setShowBidForm] = useState(false);
  const [newBid, setNewBid] = useState<BidCreateInput>({
    supplier_id: "",
    submitted_price: 0,
    local_content_score: 0,
    evaluation_formula: "SIXTY_FORTY",
  });
  const [addingBid, setAddingBid] = useState(false);

  // Run evaluation
  const [runResult, setRunResult] = useState<EvaluationRunResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);

  // ─── Load projects ────────────────────────────────────────────────
  const loadProjects = useCallback(async () => {
    setLoadingProjects(true);
    try {
      const data = await projectService.getAllProjects({ skip: 0, limit: 100 });
      setProjects(data);
      if (data.length > 0) setSelectedProjectId(data[0].id);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load projects.";
      setCriteriaError(msg);
    } finally {
      setLoadingProjects(false);
    }
  }, []);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  // ─── Load criteria + bids when a project is selected ──────────────
  const loadCriteriaAndBids = useCallback(async (projectId: string) => {
    if (!projectId) return;
    setCriteriaLoading(true);
    setBidsLoading(true);
    setCriteriaError(null);
    setRunResult(null);

    try {
      const c = await evaluationService.getCriteria(projectId);
      setCriteria(c);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load criteria.";
      setCriteriaError(msg);
      setCriteria(null);
    } finally {
      setCriteriaLoading(false);
    }

    try {
      const b = await evaluationService.listBids(projectId);
      setBids(b);
    } catch {
      setBids([]);
    } finally {
      setBidsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedProjectId) loadCriteriaAndBids(selectedProjectId);
  }, [selectedProjectId, loadCriteriaAndBids]);

  // ─── Criteria save ────────────────────────────────────────────────
  const handleSaveCriteria = async () => {
    if (!selectedProjectId || !criteria) return;
    setCriteriaSaving(true);
    setCriteriaError(null);
    try {
      const updated = await evaluationService.updateCriteria(selectedProjectId, {
        formula: criteria.formula,
        lc_weight: criteria.lc_weight,
        price_weight: criteria.price_weight,
        sme_preference_pct: criteria.sme_preference_pct,
        tadawul_bonus_pts: criteria.tadawul_bonus_pts,
        rhq_required: criteria.rhq_required,
        risk_cap_pct: criteria.risk_cap_pct,
        waiver_cap_pct: criteria.waiver_cap_pct,
      });
      setCriteria(updated);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to save criteria.";
      setCriteriaError(msg);
    } finally {
      setCriteriaSaving(false);
    }
  };

  // ─── Add bid ──────────────────────────────────────────────────────
  const handleAddBid = async () => {
    if (!selectedProjectId) return;
    if (!newBid.supplier_id.trim()) {
      setCriteriaError("Supplier ID is required.");
      return;
    }
    if (newBid.submitted_price <= 0) {
      setCriteriaError("Submitted price must be greater than 0.");
      return;
    }
    setAddingBid(true);
    setCriteriaError(null);
    try {
      await evaluationService.createBid(selectedProjectId, newBid);
      const refreshed = await evaluationService.listBids(selectedProjectId);
      setBids(refreshed);
      setShowBidForm(false);
      setNewBid({
        supplier_id: "",
        submitted_price: 0,
        local_content_score: 0,
        evaluation_formula: criteria?.formula ?? "SIXTY_FORTY",
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to add bid.";
      setCriteriaError(msg);
    } finally {
      setAddingBid(false);
    }
  };

  // ─── Run evaluation ───────────────────────────────────────────────
  const handleRunEvaluation = async () => {
    if (!selectedProjectId) return;
    setRunning(true);
    setRunError(null);
    try {
      const result = await evaluationService.runEvaluation(selectedProjectId);
      setRunResult(result);
      // Refresh bids so rank/effective_price reflect the latest run.
      const refreshed = await evaluationService.listBids(selectedProjectId);
      setBids(refreshed);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Evaluation failed.";
      setRunError(msg);
    } finally {
      setRunning(false);
    }
  };

  // ─── Render ───────────────────────────────────────────────────────
  return (
    <div className="max-w-7xl mx-auto animate-in fade-in duration-500 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-blue-900/30 border border-blue-800/50 flex items-center justify-center">
            <Scale className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-100">Bid Evaluation Engine</h1>
            <p className="text-xs text-slate-500">
              Saudi local-content scoring (60/40, 70/30, SME 10%, Tadawul, RHQ, Risk Cap)
            </p>
          </div>
        </div>
      </div>

      {/* Project selector */}
      <div className="flex items-center gap-4 bg-slate-900 border border-slate-800 rounded-lg p-4">
        <label htmlFor="project-select" className="text-sm font-medium text-slate-300 whitespace-nowrap">
          Project:
        </label>
        {loadingProjects ? (
          <Loader2 className="w-4 h-4 animate-spin text-slate-500" />
        ) : projects.length === 0 ? (
          <span className="text-sm text-slate-500">No projects available. Create one first.</span>
        ) : (
          <select
            id="project-select"
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="flex-1 bg-slate-950 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-600"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} — {p.client}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Error banner */}
      {criteriaError && (
        <div className="p-3 bg-red-950/40 border border-red-900/50 rounded-lg text-xs font-mono text-red-400 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>{criteriaError}</span>
        </div>
      )}

      {!selectedProjectId ? (
        <div className="text-center py-16 text-slate-500">
          <Scale className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p>Select a project to configure evaluation criteria and manage bids.</p>
        </div>
      ) : (
        <>
          {/* Two-column: Criteria + Bids */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* ── LEFT: Criteria ────────────────────────────────────── */}
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
                  Evaluation Criteria
                </h2>
                {criteriaSaving && (
                  <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                )}
              </div>

              {criteriaLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-slate-500" />
                </div>
              ) : criteria ? (
                <div className="space-y-4">
                  {/* Formula */}
                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">
                      Scoring Formula
                    </label>
                    <select
                      value={criteria.formula}
                      onChange={(e) =>
                        setCriteria({
                          ...criteria,
                          formula: e.target.value as EvaluationFormula,
                        })
                      }
                      className="w-full bg-slate-950 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-600"
                    >
                      {ALL_FORMULAS.map((f) => (
                        <option key={f} value={f}>
                          {FORMULA_LABELS[f]}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Weights row */}
                  <div className="grid grid-cols-2 gap-3">
                    <NumberField
                      label="LC Weight (%)"
                      value={criteria.lc_weight}
                      onChange={(v) => setCriteria({ ...criteria, lc_weight: v })}
                    />
                    <NumberField
                      label="Price Weight (%)"
                      value={criteria.price_weight}
                      onChange={(v) => setCriteria({ ...criteria, price_weight: v })}
                    />
                  </div>

                  {/* Preferences row */}
                  <div className="grid grid-cols-2 gap-3">
                    <NumberField
                      label="SME Preference (%)"
                      value={criteria.sme_preference_pct}
                      onChange={(v) =>
                        setCriteria({ ...criteria, sme_preference_pct: v })
                      }
                    />
                    <NumberField
                      label="Tadawul Bonus (pts)"
                      value={criteria.tadawul_bonus_pts}
                      onChange={(v) =>
                        setCriteria({ ...criteria, tadawul_bonus_pts: v })
                      }
                    />
                  </div>

                  {/* Caps row */}
                  <div className="grid grid-cols-2 gap-3">
                    <NumberField
                      label="Risk Cap (%)"
                      value={criteria.risk_cap_pct}
                      onChange={(v) => setCriteria({ ...criteria, risk_cap_pct: v })}
                    />
                    <NumberField
                      label="Waiver Cap (%)"
                      value={criteria.waiver_cap_pct}
                      onChange={(v) =>
                        setCriteria({ ...criteria, waiver_cap_pct: v })
                      }
                    />
                  </div>

                  {/* RHQ toggle */}
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={criteria.rhq_required}
                      onChange={(e) =>
                        setCriteria({ ...criteria, rhq_required: e.target.checked })
                      }
                      className="w-4 h-4 rounded border-slate-600 bg-slate-950 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-slate-300">
                      Require RHQ eligibility (disqualify non-RHQ suppliers)
                    </span>
                  </label>

                  <button
                    onClick={handleSaveCriteria}
                    disabled={criteriaSaving}
                    className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium py-2.5 rounded-md transition-colors"
                  >
                    <Save className="w-4 h-4" />
                    Save Criteria
                  </button>
                </div>
              ) : (
                <p className="text-sm text-slate-500 py-8 text-center">
                  Failed to load criteria.
                </p>
              )}
            </div>

            {/* ── RIGHT: Bids ──────────────────────────────────────── */}
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
                  Bids ({bids.length})
                </h2>
                <button
                  onClick={() => setShowBidForm(!showBidForm)}
                  className="flex items-center gap-1.5 text-xs font-medium text-blue-400 hover:text-blue-300 transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Add Bid
                </button>
              </div>

              {/* Inline add-bid form */}
              {showBidForm && (
                <div className="mb-4 p-4 bg-slate-950 border border-slate-700 rounded-md space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">
                      Supplier ID (UUID)
                    </label>
                    <input
                      type="text"
                      value={newBid.supplier_id}
                      onChange={(e) =>
                        setNewBid({ ...newBid, supplier_id: e.target.value })
                      }
                      placeholder="00000000-0000-0000-0000-000000000000"
                      className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-200 font-mono focus:outline-none focus:border-blue-600"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-slate-400 mb-1">
                        Submitted Price (SAR)
                      </label>
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={newBid.submitted_price || ""}
                        onChange={(e) =>
                          setNewBid({
                            ...newBid,
                            submitted_price: parseFloat(e.target.value) || 0,
                          })
                        }
                        className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-600"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-400 mb-1">
                        Local Content Score (0–100)
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        step="0.01"
                        value={newBid.local_content_score || ""}
                        onChange={(e) =>
                          setNewBid({
                            ...newBid,
                            local_content_score: parseFloat(e.target.value) || 0,
                          })
                        }
                        className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-600"
                      />
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={handleAddBid}
                      disabled={addingBid}
                      className="flex-1 flex items-center justify-center gap-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium py-2 rounded-md transition-colors"
                    >
                      {addingBid ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Plus className="w-4 h-4" />
                      )}
                      Add
                    </button>
                    <button
                      onClick={() => setShowBidForm(false)}
                      className="px-4 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium py-2 rounded-md transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {/* Bids table */}
              {bidsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-slate-500" />
                </div>
              ) : bids.length === 0 ? (
                <p className="text-sm text-slate-500 py-8 text-center">
                  No bids yet. Add one to start evaluating.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-xs text-slate-500 uppercase border-b border-slate-800">
                        <th className="text-left py-2 px-2 font-medium">Rank</th>
                        <th className="text-left py-2 px-2 font-medium">Supplier</th>
                        <th className="text-right py-2 px-2 font-medium">Price</th>
                        <th className="text-right py-2 px-2 font-medium">Eff. Price</th>
                        <th className="text-right py-2 px-2 font-medium">Score</th>
                        <th className="text-center py-2 px-2 font-medium">Flags</th>
                      </tr>
                    </thead>
                    <tbody>
                      {bids
                        .slice()
                        .sort(
                          (a, b) =>
                            (a.rank ?? 999) - (b.rank ?? 999) ||
                            (b.final_score ?? 0) - (a.final_score ?? 0),
                        )
                        .map((bid) => (
                          <tr
                            key={bid.id}
                            className="border-b border-slate-800/50 hover:bg-slate-800/30"
                          >
                            <td className="py-2.5 px-2">
                              {bid.rank ? (
                                <span
                                  className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${
                                    bid.rank === 1
                                      ? "bg-amber-500/20 text-amber-400"
                                      : "bg-slate-800 text-slate-400"
                                  }`}
                                >
                                  {bid.rank === 1 ? (
                                    <Trophy className="w-3.5 h-3.5" />
                                  ) : (
                                    bid.rank
                                  )}
                                </span>
                              ) : (
                                <span className="text-slate-600">—</span>
                              )}
                            </td>
                            <td className="py-2.5 px-2 font-mono text-xs text-slate-400">
                              {shortId(bid.supplier_id)}
                            </td>
                            <td className="py-2.5 px-2 text-right text-slate-300">
                              {formatSAR(bid.submitted_price)}
                            </td>
                            <td className="py-2.5 px-2 text-right text-slate-400">
                              {formatSAR(bid.effective_price)}
                            </td>
                            <td className="py-2.5 px-2 text-right font-mono font-semibold text-slate-200">
                              {formatScore(bid.final_score)}
                            </td>
                            <td className="py-2.5 px-2">
                              <div className="flex items-center justify-center gap-1">
                                {bid.sme_preference_applied && (
                                  <span
                                    title="SME 10% preference applied"
                                    className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-900/40 text-emerald-400 font-medium"
                                  >
                                    SME
                                  </span>
                                )}
                                {bid.tadawul_bonus_applied && (
                                  <span
                                    title="Tadawul listed bonus"
                                    className="text-[10px] px-1.5 py-0.5 rounded bg-blue-900/40 text-blue-400 font-medium"
                                  >
                                    TAD
                                  </span>
                                )}
                              </div>
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          {/* ── Run evaluation ─────────────────────────────────────── */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
                Run Evaluation
              </h2>
              <button
                onClick={handleRunEvaluation}
                disabled={running || bids.length === 0}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium px-4 py-2 rounded-md transition-colors"
              >
                {running ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                Run Evaluation
              </button>
            </div>

            {runError && (
              <div className="p-3 bg-red-950/40 border border-red-900/50 rounded-md text-xs text-red-400 mb-4">
                {runError}
              </div>
            )}

            {runResult && (
              <EvaluationResults result={runResult} bids={bids} />
            )}

            {!runResult && !running && bids.length > 0 && (
              <p className="text-sm text-slate-500 text-center py-4">
                Click "Run Evaluation" to compute scores, apply preferences, and check the risk cap.
              </p>
            )}
          </div>
        </>
      )}
    </div>
  );
}

// ─── Sub-components ──────────────────────────────────────────────────

function NumberField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-slate-400 mb-1">{label}</label>
      <input
        type="number"
        min="0"
        max="100"
        step="0.01"
        value={value || ""}
        onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
        className="w-full bg-slate-950 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-600"
      />
    </div>
  );
}

function EvaluationResults({
  result,
  bids,
}: {
  result: EvaluationRunResponse;
  bids: Bid[];
}) {
  const capAmount =
    (result.project_budget * result.risk_cap_pct) / 100;

  return (
    <div className="space-y-4">
      {/* Risk cap banner */}
      {result.risk_cap_breached ? (
        <div className="flex items-start gap-3 p-4 bg-red-950/40 border border-red-900/50 rounded-md">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-red-300">Risk Cap Breached</p>
            <p className="text-xs text-red-400 mt-1">
              Total exposure ({formatSAR(result.total_exposure)}) exceeds the risk cap of{" "}
              {result.risk_cap_pct}% of the winning bid ({formatSAR(capAmount)}).
            </p>
          </div>
        </div>
      ) : (
        <div className="flex items-start gap-3 p-4 bg-emerald-950/30 border border-emerald-900/40 rounded-md">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-emerald-300">Within Risk Cap</p>
            <p className="text-xs text-emerald-400/80 mt-1">
              Total exposure ({formatSAR(result.total_exposure)}) is within the cap of{" "}
              {result.risk_cap_pct}% of the winning bid ({formatSAR(capAmount)}).
            </p>
          </div>
        </div>
      )}

      {/* Results table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-slate-500 uppercase border-b border-slate-800">
              <th className="text-left py-2 px-2 font-medium">Rank</th>
              <th className="text-left py-2 px-2 font-medium">Supplier</th>
              <th className="text-right py-2 px-2 font-medium">Eff. Price</th>
              <th className="text-right py-2 px-2 font-medium">Price Score</th>
              <th className="text-right py-2 px-2 font-medium">Weighted</th>
              <th className="text-right py-2 px-2 font-medium">Tadawul</th>
              <th className="text-right py-2 px-2 font-medium">Final</th>
              <th className="text-center py-2 px-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {result.results
              .slice()
              .sort((a, b) => {
                // Disqualified bids sort to the end; among eligible, rank asc.
                const dq = Number(a.disqualified) - Number(b.disqualified);
                if (dq !== 0) return dq;
                return a.rank - b.rank;
              })
              .map((r) => {
                const bd = parseBreakdown(r.breakdown_json);
                const bid = bids.find((b) => b.id === r.bid_id);
                return (
                  <tr
                    key={r.id}
                    className={`border-b border-slate-800/50 ${
                      r.disqualified ? "opacity-50" : "hover:bg-slate-800/30"
                    }`}
                  >
                    <td className="py-2.5 px-2">
                      {r.disqualified ? (
                        <Ban className="w-4 h-4 text-red-400" />
                      ) : r.rank === 1 ? (
                        <Trophy className="w-4 h-4 text-amber-400" />
                      ) : (
                        <span className="text-slate-400 text-xs">{r.rank}</span>
                      )}
                    </td>
                    <td className="py-2.5 px-2 font-mono text-xs text-slate-400">
                      {shortId(bid?.supplier_id)}
                    </td>
                    <td className="py-2.5 px-2 text-right text-slate-300">
                      {formatSAR(r.effective_price)}
                    </td>
                    <td className="py-2.5 px-2 text-right text-slate-400 font-mono text-xs">
                      {bd?.price_score ? parseFloat(bd.price_score).toFixed(2) : "—"}
                    </td>
                    <td className="py-2.5 px-2 text-right text-slate-400 font-mono text-xs">
                      {bd?.weighted_score ? parseFloat(bd.weighted_score).toFixed(2) : "—"}
                    </td>
                    <td className="py-2.5 px-2 text-right text-blue-400 font-mono text-xs">
                      {bd?.tadawul_bonus_added && bd.tadawul_bonus_added !== "0"
                        ? `+${bd.tadawul_bonus_added}`
                        : "—"}
                    </td>
                    <td className="py-2.5 px-2 text-right font-mono font-bold text-slate-100">
                      {formatScore(r.final_score)}
                    </td>
                    <td className="py-2.5 px-2 text-center">
                      {r.disqualified ? (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-red-900/40 text-red-400 font-medium">
                          {r.disqualification_reason || "DQ"}
                        </span>
                      ) : r.rank === 1 ? (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-amber-900/40 text-amber-400 font-medium">
                          WINNER
                        </span>
                      ) : (
                        <span className="text-[10px] text-slate-500">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
          </tbody>
        </table>
      </div>

      {/* Summary footer */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
        <SummaryStat label="Winning Bid" value={formatSAR(result.project_budget)} />
        <SummaryStat
          label={`Risk Cap (${result.risk_cap_pct}%)`}
          value={formatSAR(capAmount)}
        />
        <SummaryStat label="Total Exposure" value={formatSAR(result.total_exposure)} />
        <SummaryStat
          label="Bids Evaluated"
          value={`${result.results.filter((r) => !r.disqualified).length}/${result.results.length}`}
        />
      </div>
    </div>
  );
}

function SummaryStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-slate-950 border border-slate-800 rounded-md p-3">
      <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">{label}</p>
      <p className="text-sm font-mono font-semibold text-slate-200">{value}</p>
    </div>
  );
}
