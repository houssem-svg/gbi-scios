// src/components/reports/ReportCard.tsx

"use client";

import { CheckCircle2, Clock, Download, FileText, ShieldAlert } from "lucide-react";
import { Report } from "@/types/report";
import { useState } from "react";

interface ReportCardProps {
  report: Report;
  onDownload: (id: number, filename: string) => Promise<void>;
}

export default function ReportCard({ report, onDownload }: ReportCardProps) {
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownload = async () => {
    setIsDownloading(true);
    try {
      await onDownload(report.id, title);
    } finally {
      setIsDownloading(false);
    }
  };

  const title = `${report.report_type === "EXECUTIVE" ? "Executive" : "Comprehensive"} Report #${report.id}`;
  const generatedAt = report.json_payload?.metadata?.generated_at || report.created_at;
  const unresolvedFlags = report.json_payload?.compliance_summary?.unresolved_violations ?? 0;
  const resolvedFlags = report.json_payload?.compliance_summary?.resolved_violations ?? 0;
  const riskScore = Math.min(
    100,
    Math.round(report.json_payload?.exposure_metrics?.exposure_percentage_vs_project_budget ?? 0)
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case "COMPLETED": return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20';
      case "PROCESSING": return 'text-blue-400 bg-blue-400/10 border-blue-400/20';
      case "FAILED": return 'text-red-400 bg-red-400/10 border-red-400/20';
      default: return 'text-slate-400 bg-slate-400/10 border-slate-400/20';
    }
  };

  const getRiskColor = (score: number) => {
    if (score >= 80) return 'text-red-400';
    if (score >= 50) return 'text-orange-400';
    if (score >= 20) return 'text-yellow-400';
    return 'text-emerald-400';
  };

  return (
    <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-5 hover:bg-slate-800/40 transition-colors group">
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-lg border ${getStatusColor(report.status)}`}>
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
            <div className="flex items-center gap-2 mt-1 text-xs text-slate-500 font-mono">
              <Clock className="w-3 h-3" />
              {new Date(generatedAt).toLocaleString()}
            </div>
          </div>
        </div>
        <span className={`px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider rounded-md border ${getStatusColor(report.status)}`}>
          {report.status}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-5 pt-4 border-t border-slate-800/60">
        <div>
          <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Risk Score</p>
          <div className={`flex items-center gap-1.5 text-lg font-mono font-bold ${getRiskColor(riskScore)}`}>
            {riskScore >= 50 ? <ShieldAlert className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
            {riskScore}%
          </div>
        </div>
        <div>
          <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Passed Checks</p>
          <p className="text-lg font-mono font-bold text-slate-300">{resolvedFlags}</p>
        </div>
        <div>
          <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Anomalies</p>
          <p className="text-lg font-mono font-bold text-slate-300">{unresolvedFlags}</p>
        </div>
      </div>

      <button
        onClick={handleDownload}
        disabled={report.status !== "COMPLETED" || isDownloading}
        className="w-full flex items-center justify-center gap-2 py-2 text-xs font-medium text-slate-300 bg-slate-950 border border-slate-800 rounded-lg hover:bg-slate-800 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isDownloading ? (
          <span className="animate-pulse">Retrieving payload...</span>
        ) : (
          <>
            <Download className="w-3.5 h-3.5" />
            Download PDF Extraction
          </>
        )}
      </button>
    </div>
  );
}
