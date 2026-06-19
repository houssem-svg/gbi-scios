// app/dashboard/page.tsx

"use client";

import { useCallback, useEffect, useState } from "react";
import {
  ShieldCheck,
  Activity,
  Briefcase,
  AlertTriangle,
  RefreshCw,
  ListChecks,
} from "lucide-react";

import { dashboardService } from "@/lib/dashboardService";
import { DashboardSummary } from "@/types/dashboard";
import MetricCard from "@/components/dashboard/MetricCard";
import ExposureChart from "@/components/dashboard/ExposureChart";

const formatCurrency = (value: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value || 0);

const formatPercent = (value: number) => `${Math.round(value ?? 0)}%`;

export default function ExecutiveDashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchDashboardData = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    setIsRefreshing(true);
    setError(null);
    try {
      const data = await dashboardService.getSummary();
      setSummary(data);
      setLastRefreshed(new Date());
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      setError(`Failed to fetch dashboard summary: ${msg}`);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
    // FE-2: keep the 60s auto-refresh but gate on document visibility so a
    // hidden tab does not keep hammering the backend.
    const interval = setInterval(() => {
      if (document.visibilityState === "visible") {
        fetchDashboardData(true);
      }
    }, 60000);
    return () => clearInterval(interval);
  }, [fetchDashboardData]);

  // Loading skeleton.
  if (loading && !summary) {
    return (
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="h-8 w-64 bg-slate-900/50 rounded animate-pulse mb-8"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-slate-900/50 rounded-xl animate-pulse"></div>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-[400px] bg-slate-900/50 rounded-xl animate-pulse"></div>
          <div className="h-[400px] bg-slate-900/50 rounded-xl animate-pulse"></div>
        </div>
      </div>
    );
  }

  const breakdown = summary?.compliance_breakdown;
  const topRisks = summary?.top_risk_projects ?? [];

  return (
    <div className="max-w-7xl mx-auto animate-in fade-in duration-500 space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Executive Dashboard</h1>
          <p className="text-sm text-slate-400 mt-1">
            Live enterprise compliance and risk telemetry.
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-500">
          <span>Last sync: {lastRefreshed.toLocaleTimeString()}</span>
          <button
            onClick={() => fetchDashboardData(false)}
            disabled={isRefreshing}
            className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 hover:text-white transition-colors disabled:opacity-50"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-950/40 border border-red-900/50 rounded-lg text-xs font-mono text-red-400 break-words">
          SYSTEM_ERROR_STATE: {error}
        </div>
      )}

      {summary && (
        <>
          {/* Metric cards from real backend fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricCard
              title="Total Projects"
              value={summary.total_projects}
              icon={<Briefcase className="w-5 h-5" />}
            />
            <MetricCard
              title="Total Budget Managed"
              value={formatCurrency(summary.total_budget_managed)}
              icon={<ShieldCheck className="w-5 h-5" />}
            />
            <MetricCard
              title="Total Financial Exposure"
              value={formatCurrency(summary.total_financial_exposure)}
              icon={<AlertTriangle className="w-5 h-5" />}
              isNegativeGood
            />
            <MetricCard
              title="Overall Compliance Score"
              value={formatPercent(summary.overall_compliance_score)}
              icon={<Activity className="w-5 h-5" />}
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Exposure chart sourced from top_risk_projects */}
            <div className="lg:col-span-2 bg-slate-900/40 border border-slate-800 rounded-xl p-5">
              <h3 className="text-sm font-semibold text-slate-200 mb-1">Top Risk Projects — Exposure</h3>
              <p className="text-xs text-slate-500 mb-4">
                Financial exposure per top-risk project (red &gt; 1M, orange &gt; 100K).
              </p>
              <ExposureChart data={topRisks} />
            </div>

            {/* Compliance breakdown */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-5 flex flex-col">
              <div className="flex items-center gap-2 mb-4">
                <ListChecks className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-semibold text-slate-200">Compliance Breakdown</h3>
              </div>
              <div className="flex-1 space-y-3">
                <BreakdownRow label="Open flags" value={breakdown?.open_flags ?? 0} tone="red" />
                <BreakdownRow
                  label="Resolved flags"
                  value={breakdown?.resolved_flags ?? 0}
                  tone="emerald"
                />
                <BreakdownRow
                  label="Waived flags"
                  value={breakdown?.waived_flags ?? 0}
                  tone="amber"
                />
                <div className="pt-3 mt-3 border-t border-slate-800">
                  <div className="flex items-center justify-between">
                    <span className="text-xs uppercase tracking-wider text-slate-500 font-medium">
                      Total flags
                    </span>
                    <span className="text-lg font-mono font-bold text-slate-100">
                      {breakdown?.total_flags ?? 0}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Top risk projects table */}
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-800">
              <h3 className="text-sm font-semibold text-slate-200">Top Risk Projects</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Projects with the highest exposure and flag counts.
              </p>
            </div>
            {topRisks.length === 0 ? (
              <div className="p-10 text-center text-sm text-slate-500">
                No risk-bearing projects detected.
              </div>
            ) : (
              <div className="overflow-x-auto max-h-96 overflow-y-auto">
                <table className="w-full text-left text-sm whitespace-nowrap">
                  <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 sticky top-0">
                    <tr>
                      <th className="px-6 py-3 font-medium uppercase tracking-wider text-xs">
                        Project
                      </th>
                      <th className="px-6 py-3 font-medium uppercase tracking-wider text-xs">
                        Exposure
                      </th>
                      <th className="px-6 py-3 font-medium uppercase tracking-wider text-xs">
                        Flags
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {topRisks.map((p) => (
                      <tr key={p.project_id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="px-6 py-3">
                          <div className="font-medium text-slate-200">{p.project_name || "—"}</div>
                          <div className="text-xs text-slate-500 font-mono mt-0.5">
                            {p.project_id}
                          </div>
                        </td>
                        <td className="px-6 py-3 font-mono font-semibold text-slate-100">
                          {formatCurrency(p.project_exposure)}
                        </td>
                        <td className="px-6 py-3">
                          <span
                            className={`px-2.5 py-0.5 rounded-md text-xs font-medium border ${
                              p.flag_count > 5
                                ? "bg-red-950/50 text-red-400 border-red-900/50"
                                : p.flag_count > 0
                                  ? "bg-orange-950/50 text-orange-400 border-orange-900/50"
                                  : "bg-emerald-950/50 text-emerald-400 border-emerald-900/50"
                            }`}
                          >
                            {p.flag_count}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

interface BreakdownRowProps {
  label: string;
  value: number;
  tone: "red" | "emerald" | "amber";
}

function BreakdownRow({ label, value, tone }: BreakdownRowProps) {
  const toneClasses: Record<BreakdownRowProps["tone"], string> = {
    red: "text-red-400 bg-red-950/30 border-red-900/40",
    emerald: "text-emerald-400 bg-emerald-950/30 border-emerald-900/40",
    amber: "text-amber-400 bg-amber-950/30 border-amber-900/40",
  };
  return (
    <div className="flex items-center justify-between p-3 rounded-lg border border-slate-800/80 bg-slate-950/40">
      <span className="text-xs text-slate-300">{label}</span>
      <span className={`text-sm font-mono font-bold px-2 py-0.5 rounded border ${toneClasses[tone]}`}>
        {value}
      </span>
    </div>
  );
}

