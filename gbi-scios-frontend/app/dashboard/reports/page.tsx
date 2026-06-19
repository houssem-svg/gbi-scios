// src/app/dashboard/reports/page.tsx

"use client";

import { useCallback, useEffect, useState } from "react";
import { Activity, ShieldCheck, AlertOctagon, FileLineChart, Loader2 } from "lucide-react";
import { reportingService } from "@/lib/reportingService";
import { projectService } from "@/lib/projectService";
import { Report } from "@/types/report";
import { Project } from "@/types/project";
import ReportCard from "@/components/reports/ReportCard";
import Pagination from "@/components/common/Pagination";

const REPORTS_PAGE_SIZE = 9;

export default function SovereignReportsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");

  const [reports, setReports] = useState<Report[]>([]);
  const [reportsPage, setReportsPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // FE-15 (useCallback + exhaustive-deps): project list loader is stable.
  const loadProjects = useCallback(async () => {
    try {
      const data = await projectService.getAllProjects({
        skip: 0,
        limit: 100,
      });
      setProjects(data);
      if (data.length > 0) setSelectedProjectId(data[0].id);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      setError(`Failed to fetch project bounds: ${msg}`);
    }
  }, []);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  // FE-15: reports loader is wrapped in useCallback so it can be a dep
  // of the selectedProjectId effect without re-creating each render.
  const fetchReports = useCallback(
    async (projectId: string) => {
      setLoading(true);
      setError(null);
      try {
        const data: Report[] = await reportingService.getReportsByProject(
          projectId,
          { skip: 0, limit: 100 },
        );
        const reportsArray = Array.isArray(data)
          ? data
          : (data as unknown as { reports?: Report[] })?.reports ??
            (data as unknown as { data?: Report[] })?.data ??
            [];
        if (Array.isArray(reportsArray)) {
          setReports(
            [...reportsArray].sort(
              (a, b) =>
                new Date(b.created_at).getTime() -
                new Date(a.created_at).getTime(),
            ),
          );
        } else {
          setReports([]);
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Unknown error";
        setError(`Failed to synchronize reporting telemetry: ${msg}`);
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    if (!selectedProjectId) return;
    setReportsPage(1);
    fetchReports(selectedProjectId);
  }, [selectedProjectId, fetchReports]);

  const handleGenerateReport = async () => {
    if (!selectedProjectId) return;
    setIsGenerating(true);
    setError(null);
    try {
      await reportingService.generateReport({ project_id: selectedProjectId });
      await fetchReports(selectedProjectId);
      setReportsPage(1);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Engine failed to compile report matrix.";
      setError(msg);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = async (id: number, filename: string) => {
    try {
      await reportingService.downloadReport(id, filename);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to establish download stream.";
      alert(msg);
    }
  };

  // Metrics Calculation (computed over the full list — not just the page).
  const getReportRiskScore = (report: Report) =>
    Math.min(100, Math.round(report.json_payload?.exposure_metrics?.exposure_percentage_vs_project_budget ?? 0));
  const avgRisk = reports.length ? Math.round(reports.reduce((acc, curr) => acc + getReportRiskScore(curr), 0) / reports.length) : 0;
  const completedReports = reports.filter((r) => r.status === "COMPLETED").length;
  const criticalFindings = reports.reduce(
    (acc, curr) => acc + (curr.json_payload?.compliance_summary?.unresolved_violations || 0),
    0,
  );

  // FE-15: client-side pagination slice.
  const totalReports = reports.length;
  const totalPages = Math.max(1, Math.ceil(totalReports / REPORTS_PAGE_SIZE));
  const safePage = Math.min(Math.max(1, reportsPage), totalPages);
  const startIdx = (safePage - 1) * REPORTS_PAGE_SIZE;
  const pagedReports = reports.slice(startIdx, startIdx + REPORTS_PAGE_SIZE);

  return (
    <div className="max-w-7xl mx-auto animate-in fade-in duration-500 space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Sovereign Reports</h1>
          <p className="text-sm text-slate-400 mt-1">Compile and extract executive compliance artifacts.</p>
        </div>
        <div className="flex items-center gap-3 w-full md:w-auto">
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="w-full md:w-64 px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
          >
            <option value="" disabled>Target Deployment Boundary</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
          <button
            onClick={handleGenerateReport}
            disabled={isGenerating || !selectedProjectId}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-all disabled:opacity-50 shadow-lg shadow-blue-900/20 whitespace-nowrap"
          >
            {isGenerating ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileLineChart className="w-4 h-4" />}
            Compile Report
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-950/40 border border-red-900/50 rounded-lg text-xs font-mono text-red-400 break-words">
          SYSTEM_ERROR_STATE: {error}
        </div>
      )}

      {/* Analytics Widgets */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-5 bg-slate-900/50 border border-slate-800 rounded-xl flex items-center gap-4">
          <div className="p-3 bg-blue-950/30 text-blue-400 rounded-lg border border-blue-900/30">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider font-medium">Compiled Artifacts</p>
            <h4 className="text-2xl font-bold text-slate-100 mt-1">{completedReports}</h4>
          </div>
        </div>
        <div className="p-5 bg-slate-900/50 border border-slate-800 rounded-xl flex items-center gap-4">
          <div className="p-3 bg-emerald-950/30 text-emerald-400 rounded-lg border border-emerald-900/30">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider font-medium">Mean Risk Quotient</p>
            <h4 className="text-2xl font-bold text-slate-100 mt-1">{avgRisk}%</h4>
          </div>
        </div>
        <div className="p-5 bg-slate-900/50 border border-slate-800 rounded-xl flex items-center gap-4">
          <div className="p-3 bg-orange-950/30 text-orange-400 rounded-lg border border-orange-900/30">
            <AlertOctagon className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider font-medium">Total Anomalies</p>
            <h4 className="text-2xl font-bold text-slate-100 mt-1">{criticalFindings}</h4>
          </div>
        </div>
      </div>

      {/* Reports Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-48 bg-slate-900/50 border border-slate-800 rounded-xl animate-pulse"></div>
          ))}
        </div>
      ) : reports.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-16 bg-slate-900/30 border border-slate-800 border-dashed rounded-xl text-center">
          <div className="p-3 bg-slate-900 rounded-xl border border-slate-800 mb-4 text-slate-500">
            <FileLineChart className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-medium text-slate-300">No Intelligence Reports</h3>
          <p className="text-xs text-slate-500 max-w-sm mt-1">Compile an executive report to extract compliance and risk metrics.</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {pagedReports.map((report) => (
              <ReportCard key={report.id} report={report} onDownload={handleDownload} />
            ))}
          </div>
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
            <Pagination
              page={safePage}
              pageSize={REPORTS_PAGE_SIZE}
              total={totalReports}
              onPageChange={setReportsPage}
            />
          </div>
        </>
      )}
    </div>
  );
}
