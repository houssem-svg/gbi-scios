"use client";

import { useCallback, useEffect, useState } from "react";
import {
  ShieldAlert,
  Loader2,
  Play,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Gavel,
  RefreshCw,
} from "lucide-react";
import { projectService } from "@/lib/projectService";
import { complianceService } from "@/lib/complianceService";
import type { Project } from "@/types/project";
import type {
  ComplianceFlag,
  ComplianceFlagStatus,
  ComplianceScanResult,
} from "@/types/compliance";

function formatSAR(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "SAR",
    maximumFractionDigits: 0,
  }).format(value || 0);
}

const STATUS_STYLES: Record<ComplianceFlagStatus, { label: string; cls: string }> = {
  open: { label: "OPEN", cls: "bg-red-900/40 text-red-400" },
  waived: { label: "WAIVED", cls: "bg-amber-900/40 text-amber-400" },
  resolved: { label: "RESOLVED", cls: "bg-emerald-900/40 text-emerald-400" },
};

export default function CompliancePage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [flags, setFlags] = useState<ComplianceFlag[]>([]);
  const [scanResult, setScanResult] = useState<ComplianceScanResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [waivingFlagId, setWaivingFlagId] = useState<string | null>(null);
  const [waiverModal, setWaiverModal] = useState<{
    flagId: string;
    flagCode: string;
  } | null>(null);
  const [waiverReason, setWaiverReason] = useState("");

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

  // Load flags when project changes
  const loadFlags = useCallback(async (projectId: string) => {
    if (!projectId) return;
    setError(null);
    try {
      const data = await complianceService.listFlags(projectId, {
        skip: 0,
        limit: 200,
      });
      setFlags(data);
    } catch {
      setFlags([]);
    }
  }, []);

  useEffect(() => {
    if (selectedProjectId) loadFlags(selectedProjectId);
    else setFlags([]);
  }, [selectedProjectId, loadFlags]);

  // Run scan
  const handleScan = async () => {
    if (!selectedProjectId) return;
    setScanning(true);
    setError(null);
    setScanResult(null);
    try {
      const result = await complianceService.scanProject(selectedProjectId);
      setScanResult(result);
      setFlags(result.flags);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scan failed.");
    } finally {
      setScanning(false);
    }
  };

  // Waive a flag
  const handleWaive = async () => {
    if (!waiverModal || !waiverReason.trim()) return;
    setWaivingFlagId(waiverModal.flagId);
    setError(null);
    try {
      const updated = await complianceService.updateFlagStatus(
        waiverModal.flagId,
        {
          status: "waived",
          waiver_reason: waiverReason.trim(),
        },
      );
      setFlags((prev) =>
        prev.map((f) => (f.id === updated.id ? updated : f)),
      );
      setWaiverModal(null);
      setWaiverReason("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Waiver failed.");
    } finally {
      setWaivingFlagId(null);
    }
  };

  // Resolve a flag
  const handleResolve = async (flagId: string) => {
    const reason = prompt("Enter resolution note:");
    if (!reason || reason.trim().length < 3) return;
    setWaivingFlagId(flagId);
    try {
      const updated = await complianceService.updateFlagStatus(flagId, {
        status: "resolved",
        waiver_reason: reason.trim(),
      });
      setFlags((prev) => prev.map((f) => (f.id === updated.id ? updated : f)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Resolve failed.");
    } finally {
      setWaivingFlagId(null);
    }
  };

  const openFlags = flags.filter((f) => f.status === "open");
  const waivedFlags = flags.filter((f) => f.status === "waived");
  const resolvedFlags = flags.filter((f) => f.status === "resolved");
  const totalExposure = openFlags.reduce(
    (sum, f) => sum + (f.exposure_amount || 0),
    0,
  );

  return (
    <div className="max-w-7xl mx-auto animate-in fade-in duration-500 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-red-900/30 border border-red-800/50 flex items-center justify-center">
            <ShieldAlert className="w-5 h-5 text-red-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-100">Compliance & Gap Analysis</h1>
            <p className="text-xs text-slate-500">
              Scan imported BoQ items against the mandatory list — flag violations, request waivers.
            </p>
          </div>
        </div>
        <button
          onClick={handleScan}
          disabled={scanning || !selectedProjectId}
          className="flex items-center gap-2 bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-md transition-colors"
        >
          {scanning ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Play className="w-4 h-4" />
          )}
          Run Compliance Scan
        </button>
      </div>

      {/* Project selector */}
      <div className="flex items-center gap-4 bg-slate-900 border border-slate-800 rounded-lg p-4">
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
      </div>

      {/* Error banner */}
      {error && (
        <div className="flex items-start gap-2 p-3 bg-red-950/40 border border-red-900/50 rounded-lg text-xs text-red-400">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Summary cards */}
      {scanResult && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <SummaryCard
            label="Scanned Items"
            value={String(scanResult.total_scanned_items)}
            icon={<RefreshCw className="w-4 h-4 text-slate-400" />}
          />
          <SummaryCard
            label="Violations"
            value={String(scanResult.matched_violations)}
            icon={<XCircle className="w-4 h-4 text-red-400" />}
          />
          <SummaryCard
            label="Open Exposure"
            value={formatSAR(totalExposure)}
            icon={<AlertTriangle className="w-4 h-4 text-amber-400" />}
          />
          <SummaryCard
            label="Status"
            value={scanResult.compliance_status === "compliant" ? "Compliant" : "Violations Found"}
            icon={
              scanResult.compliance_status === "compliant" ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              ) : (
                <XCircle className="w-4 h-4 text-red-400" />
              )
            }
          />
        </div>
      )}

      {/* Flags table */}
      {!selectedProjectId ? (
        <div className="text-center py-16 text-slate-500">
          <ShieldAlert className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p>Select a project to view compliance flags.</p>
        </div>
      ) : flags.length === 0 ? (
        <div className="text-center py-16 text-slate-500 bg-slate-900 border border-slate-800 rounded-lg">
          <CheckCircle2 className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-sm">No compliance flags. Run a scan to detect violations.</p>
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
              Red Flags ({flags.length})
            </h2>
            <div className="flex gap-3 text-xs text-slate-500">
              <span className="text-red-400">● {openFlags.length} open</span>
              <span className="text-amber-400">● {waivedFlags.length} waived</span>
              <span className="text-emerald-400">● {resolvedFlags.length} resolved</span>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-slate-500 uppercase border-b border-slate-800">
                  <th className="text-left py-3 px-4 font-medium">Item Code</th>
                  <th className="text-left py-3 px-4 font-medium">Description</th>
                  <th className="text-left py-3 px-4 font-medium">Mandatory Product</th>
                  <th className="text-right py-3 px-4 font-medium">Penalty %</th>
                  <th className="text-right py-3 px-4 font-medium">Exposure</th>
                  <th className="text-center py-3 px-4 font-medium">Status</th>
                  <th className="text-center py-3 px-4 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {flags.map((flag) => {
                  const statusStyle = STATUS_STYLES[flag.status];
                  return (
                    <tr
                      key={flag.id}
                      className="border-b border-slate-800/50 hover:bg-slate-800/30"
                    >
                      <td className="py-3 px-4 font-mono text-xs text-slate-400">
                        {flag.boq_item_code || "—"}
                      </td>
                      <td className="py-3 px-4 text-slate-300 max-w-xs truncate">
                        {flag.boq_description || "—"}
                      </td>
                      <td className="py-3 px-4 text-slate-400 max-w-xs truncate">
                        {flag.mandatory_product_name || "—"}
                      </td>
                      <td className="py-3 px-4 text-right text-slate-400">
                        {(flag.penalty_percentage * 100).toFixed(0)}%
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-semibold text-red-400">
                        {formatSAR(flag.exposure_amount)}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded font-medium ${statusStyle.cls}`}
                        >
                          {statusStyle.label}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center justify-center gap-1">
                          {flag.status === "open" && (
                            <>
                              <button
                                onClick={() =>
                                  setWaiverModal({
                                    flagId: flag.id,
                                    flagCode: flag.boq_item_code || "this item",
                                  })
                                }
                                disabled={waivingFlagId === flag.id}
                                title="Request waiver"
                                className="flex items-center gap-1 text-[11px] px-2 py-1 rounded bg-amber-900/40 text-amber-400 hover:bg-amber-900/60 transition-colors disabled:opacity-50"
                              >
                                {waivingFlagId === flag.id ? (
                                  <Loader2 className="w-3 h-3 animate-spin" />
                                ) : (
                                  <Gavel className="w-3 h-3" />
                                )}
                                Waive
                              </button>
                              <button
                                onClick={() => handleResolve(flag.id)}
                                disabled={waivingFlagId === flag.id}
                                title="Mark resolved"
                                className="flex items-center gap-1 text-[11px] px-2 py-1 rounded bg-emerald-900/40 text-emerald-400 hover:bg-emerald-900/60 transition-colors disabled:opacity-50"
                              >
                                <CheckCircle2 className="w-3 h-3" />
                                Resolve
                              </button>
                            </>
                          )}
                          {flag.status === "waived" && (
                            <span className="text-[10px] text-amber-500/70 italic max-w-[150px] truncate">
                              {flag.waiver_reason || "waived"}
                            </span>
                          )}
                          {flag.status === "resolved" && (
                            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Waiver modal */}
      {waiverModal && (
        <div
          className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
          onClick={() => setWaiverModal(null)}
        >
          <div
            className="bg-slate-900 border border-slate-700 rounded-lg p-6 max-w-md w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-2 mb-4">
              <Gavel className="w-5 h-5 text-amber-400" />
              <h3 className="text-sm font-semibold text-slate-100">
                Request Waiver for {waiverModal.flagCode}
              </h3>
            </div>
            <p className="text-xs text-slate-500 mb-3">
              Provide a justification. The system enforces a 10% waiver cap of the project budget.
            </p>
            <textarea
              value={waiverReason}
              onChange={(e) => setWaiverReason(e.target.value)}
              placeholder="e.g. No local manufacturer available for this specialized component; supplier development plan in place."
              rows={4}
              className="w-full bg-slate-950 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-amber-600 resize-none"
              autoFocus
            />
            <div className="flex gap-2 mt-4">
              <button
                onClick={handleWaive}
                disabled={!waiverReason.trim() || waivingFlagId !== null}
                className="flex-1 flex items-center justify-center gap-1.5 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white text-sm font-medium py-2 rounded-md transition-colors"
              >
                {waivingFlagId ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Gavel className="w-4 h-4" />
                )}
                Submit Waiver
              </button>
              <button
                onClick={() => {
                  setWaiverModal(null);
                  setWaiverReason("");
                }}
                className="px-4 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium py-2 rounded-md transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function SummaryCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-1">
        {icon}
        <p className="text-[10px] uppercase tracking-wider text-slate-500">{label}</p>
      </div>
      <p className="text-lg font-mono font-bold text-slate-100">{value}</p>
    </div>
  );
}
