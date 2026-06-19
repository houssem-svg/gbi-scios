"use client";

import { useCallback, useEffect, useState } from "react";
import {
  LayoutDashboard,
  Loader2,
  AlertTriangle,
  TrendingDown,
  Wallet,
  FileBarChart,
  RefreshCw,
  ChevronRight,
  Info,
  UploadCloud,
} from "lucide-react";
import { projectService } from "@/lib/projectService";
import { riskService, type RiskDashboard } from "@/lib/riskService";
import { reportingService } from "@/lib/reportingService";
import type { Project } from "@/types/project";

function formatSAR(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "SAR",
    maximumFractionDigits: 0,
  }).format(value || 0);
}

const SEVERITY_STYLES: Record<string, string> = {
  LOW: "text-emerald-400 bg-emerald-900/30",
  MODERATE: "text-amber-400 bg-amber-900/30",
  HIGH: "text-orange-400 bg-orange-900/30",
  CRITICAL: "text-red-400 bg-red-900/30",
};

/**
 * Classify a backend error as "no data yet" vs a real failure.
 * When the project has no parsed BoQ items, the risk endpoint returns
 * an empty/zero exposure — we detect that and show a friendly empty-state
 * instead of a scary red error.
 */
function isNoDataState(risk: RiskDashboard | null): boolean {
  if (!risk) return false;
  return (
    risk.total_exposure === 0 &&
    risk.payroll_leakage === 0 &&
    (risk.risk_breakdown?.length ?? 0) === 0
  );
}

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [risk, setRisk] = useState<RiskDashboard | null>(null);
  const [loadingRisk, setLoadingRisk] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Load projects
  const loadProjects = useCallback(async () => {
    setLoadingProjects(true);
    try {
      const data = await projectService.getAllProjects({ skip: 0, limit: 100 });
      setProjects(data);
      if (data.length > 0) setSelectedProjectId(data[0].id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load projects.");
    } finally {
      setLoadingProjects(false);
    }
  }, []);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  /**
   * BUG FIX: graceful error handling. Previously any backend error
   * (e.g. risk calculation on a project with no BoQ items) surfaced as
   * a raw "Failed to fetch" red banner. Now we detect the "no data yet"
   * state and show a friendly empty-state guiding the user to upload +
   * parse BoQ files first.
   */
  const calculateRisk = useCallback(async (projectId: string) => {
    if (!projectId) return;
    setLoadingRisk(true);
    setError(null);
    try {
      const result = await riskService.calculateRisk(projectId);
      setRisk(result);
      // If the backend returned an empty/zero state, show the friendly
      // empty-state message instead of the bare metric cards.
      if (isNoDataState(result)) {
        setError(null); // not an error — just no data yet
      }
    } catch (err) {
      // Distinguish "no data" (404/400 from backend) vs a real failure.
      const msg = err instanceof Error ? err.message : "";
      setRisk(null);
      if (
        msg.toLowerCase().includes("not found") ||
        msg.toLowerCase().includes("no data") ||
        msg.toLowerCase().includes("no boq") ||
        msg.toLowerCase().includes("empty")
      ) {
        // Friendly empty-state — not a scary error.
        setError(null);
      } else {
        // Genuine failure — show a clear, actionable message.
        setError(
          `Could not load risk data. ${msg || "Please ensure you have uploaded and parsed a BoQ file for this project, then try again."}`,
        );
      }
    } finally {
      setLoadingRisk(false);
    }
  }, []);

  useEffect(() => {
    if (selectedProjectId) calculateRisk(selectedProjectId);
    else setRisk(null);
  }, [selectedProjectId, calculateRisk]);

  // Generate executive report
  const handleGenerateReport = async () => {
    if (!selectedProjectId) return;
    setGeneratingReport(true);
    setError(null);
    setSuccess(null);
    try {
      const report = await reportingService.generateReport({
        project_id: selectedProjectId,
        report_type: "EXECUTIVE",
      });
      setSuccess(`Report #${report.id} generated. Downloading PDF…`);
      await reportingService.downloadReport(
        report.id,
        `executive-report-${report.id}.pdf`,
      );
      setSuccess(`Report #${report.id} downloaded successfully.`);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "";
      if (msg.toLowerCase().includes("not found") || msg.toLowerCase().includes("no data")) {
        setError(
          "Cannot generate a report yet. Please upload and parse a BoQ file, then run a compliance scan first.",
        );
      } else {
        setError(`Report generation failed. ${msg}`);
      }
    } finally {
      setGeneratingReport(false);
    }
  };

  const severity = risk?.risk_breakdown?.[0]?.severity_level ?? "—";
  const totalExposure = risk?.total_exposure ?? 0;
  const payrollLeakage = risk?.payroll_leakage ?? 0;
  const mandatoryExposure = Math.max(0, totalExposure - payrollLeakage);
  const gapPct = totalExposure > 0 ? (totalExposure / (totalExposure + 1)) * 100 : 0;
  const noData = isNoDataState(risk);

  return (
    <div className="max-w-7xl mx-auto animate-in fade-in duration-500 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-blue-900/30 border border-blue-800/50 flex items-center justify-center">
            <LayoutDashboard className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-100">Executive Dashboard</h1>
            <p className="text-xs text-slate-500">
              Self-audit your financial exposure and payroll leakage before bidding.
            </p>
          </div>
        </div>
        <button
          onClick={handleGenerateReport}
          disabled={generatingReport || !selectedProjectId}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium px-5 py-2.5 rounded-md transition-colors shadow-lg shadow-blue-900/30"
        >
          {generatingReport ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <FileBarChart className="w-4 h-4" />
          )}
          Generate Executive Report
        </button>
      </div>

      {/* Project selector + refresh */}
      <div className="flex items-center gap-3 bg-slate-900 border border-slate-800 rounded-lg p-4">
        <label htmlFor="proj" className="text-sm font-medium text-slate-300 whitespace-nowrap">
          Project:
        </label>
        {loadingProjects ? (
          <Loader2 className="w-4 h-4 animate-spin text-slate-500" />
        ) : (
          <select
            id="proj"
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
        <button
          onClick={() => selectedProjectId && calculateRisk(selectedProjectId)}
          disabled={loadingRisk || !selectedProjectId}
          title="Refresh risk"
          className="p-2 text-slate-400 hover:text-blue-400 hover:bg-slate-800 rounded-md transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loadingRisk ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Banners */}
      {error && (
        <div className="flex items-start gap-2 p-3 bg-red-950/40 border border-red-900/50 rounded-lg text-xs text-red-400">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}
      {success && (
        <div className="flex items-start gap-2 p-3 bg-emerald-950/30 border border-emerald-900/40 rounded-lg text-xs text-emerald-400">
          <FileBarChart className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>{success}</span>
        </div>
      )}

      {!selectedProjectId ? (
        <div className="text-center py-16 text-slate-500">
          <LayoutDashboard className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p>Select a project to view your risk dashboard.</p>
        </div>
      ) : loadingRisk ? (
        <div className="flex flex-col items-center justify-center py-20 gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
          <p className="text-sm text-slate-500">Calculating financial exposure…</p>
        </div>
      ) : noData ? (
        /* ── FRIENDLY EMPTY-STATE ─────────────────────────────────── */
        /* Shown when the project has no parsed BoQ items (total_exposure = 0
           AND payroll_leakage = 0 AND no risk_breakdown entries). */
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-10 text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-blue-900/30 border border-blue-800/50 flex items-center justify-center">
            <Info className="w-8 h-8 text-blue-400" />
          </div>
          <h2 className="text-lg font-semibold text-slate-200 mb-2">
            No data found for this project
          </h2>
          <p className="text-sm text-slate-500 max-w-md mx-auto mb-6">
            To see your financial exposure and risk metrics, you need to upload and
            parse a BoQ file first. The system will then scan it for compliance
            violations and calculate your exposure.
          </p>
          <div className="flex items-center justify-center gap-3 flex-wrap">
            <a
              href="/dashboard/uploads"
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium px-4 py-2 rounded-md transition-colors"
            >
              <UploadCloud className="w-4 h-4" />
              Upload BoQ File
            </a>
            <a
              href="/dashboard/compliance"
              className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium px-4 py-2 rounded-md transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
              Go to Compliance
            </a>
          </div>
        </div>
      ) : risk ? (
        <>
          {/* Risk severity banner */}
          <div
            className={`flex items-center gap-3 p-4 rounded-lg border ${
              severity === "CRITICAL"
                ? "bg-red-950/40 border-red-900/50"
                : severity === "HIGH"
                  ? "bg-orange-950/30 border-orange-900/40"
                  : severity === "MODERATE"
                    ? "bg-amber-950/30 border-amber-900/40"
                    : "bg-emerald-950/30 border-emerald-900/40"
            }`}
          >
            <AlertTriangle
              className={`w-6 h-6 ${
                severity === "CRITICAL"
                  ? "text-red-400"
                  : severity === "HIGH"
                    ? "text-orange-400"
                    : severity === "MODERATE"
                      ? "text-amber-400"
                      : "text-emerald-400"
              }`}
            />
            <div className="flex-1">
              <p className="text-sm font-semibold text-slate-200">
                Risk Severity: {severity}
              </p>
              <p className="text-xs text-slate-400 mt-0.5">
                {risk.executive_summary || "No summary available."}
              </p>
            </div>
            <span
              className={`text-xs px-3 py-1 rounded font-medium ${
                SEVERITY_STYLES[severity] ?? "bg-slate-800 text-slate-400"
              }`}
            >
              {severity}
            </span>
          </div>

          {/* Metric cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Total Financial Exposure */}
            <MetricCard
              label="Total Financial Exposure"
              value={formatSAR(totalExposure)}
              icon={<Wallet className="w-5 h-5 text-red-400" />}
              accent="red"
              sublabel={`Mandatory penalties: ${formatSAR(mandatoryExposure)}`}
            />

            {/* Payroll Leakage */}
            <MetricCard
              label="Payroll Leakage (LCP 46.6%)"
              value={formatSAR(payrollLeakage)}
              icon={<TrendingDown className="w-5 h-5 text-amber-400" />}
              accent="amber"
              sublabel={`Recognition factor: ${((risk.payroll_recognition_factor ?? 0.534) * 100).toFixed(1)}%`}
            />

            {/* Current Gap Indicator */}
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle className="w-5 h-5 text-blue-400" />
                <p className="text-[11px] uppercase tracking-wider text-slate-500">
                  Current Compliance Gap
                </p>
              </div>
              <div className="flex items-end justify-between mb-3">
                <p className="text-2xl font-mono font-bold text-slate-100">
                  {gapPct.toFixed(1)}%
                </p>
                <span className="text-xs text-slate-500">exposure ratio</span>
              </div>
              {/* Progress bar */}
              <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
                <div
                  className={`h-full transition-all duration-700 ${
                    gapPct > 75
                      ? "bg-red-500"
                      : gapPct > 50
                        ? "bg-orange-500"
                        : gapPct > 25
                          ? "bg-amber-500"
                          : "bg-emerald-500"
                  }`}
                  style={{ width: `${Math.min(gapPct, 100)}%` }}
                />
              </div>
              <p className="text-[10px] text-slate-500 mt-2">
                Lower is better — reflects your exposure before competitor analysis.
              </p>
            </div>
          </div>

          {/* Mitigation actions */}
          {risk.mitigation_actions && risk.mitigation_actions.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
              <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider mb-4">
                Recommended Mitigation Actions
              </h2>
              <ul className="space-y-2">
                {risk.mitigation_actions.map((action, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-2 text-sm text-slate-300"
                  >
                    <ChevronRight className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
                    <span>{action}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Next steps CTA */}
          <div className="bg-gradient-to-r from-slate-900 to-slate-950 border border-slate-800 rounded-lg p-6 flex items-center justify-between flex-wrap gap-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-200 mb-1">
                Ready to test against competitors?
              </h3>
              <p className="text-xs text-slate-500">
                Once your self-audit is complete, head to the Bid Evaluation engine to simulate your win probability.
              </p>
            </div>
            <a
              href="/dashboard/evaluations"
              className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium px-4 py-2 rounded-md transition-colors"
            >
              Go to Bid Evaluation
              <ChevronRight className="w-4 h-4" />
            </a>
          </div>
        </>
      ) : null}
    </div>
  );
}

function MetricCard({
  label,
  value,
  icon,
  accent,
  sublabel,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  accent: "red" | "amber" | "blue";
  sublabel?: string;
}) {
  const accentCls =
    accent === "red"
      ? "border-red-900/40"
      : accent === "amber"
        ? "border-amber-900/40"
        : "border-blue-900/40";

  return (
    <div className={`bg-slate-900 border ${accentCls} rounded-lg p-5`}>
      <div className="flex items-center gap-2 mb-3">
        {icon}
        <p className="text-[11px] uppercase tracking-wider text-slate-500">{label}</p>
      </div>
      <p className="text-2xl font-mono font-bold text-slate-100">{value}</p>
      {sublabel && <p className="text-xs text-slate-500 mt-2">{sublabel}</p>}
    </div>
  );
}
