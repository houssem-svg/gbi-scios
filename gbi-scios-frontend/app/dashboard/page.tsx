// app/dashboard/page.tsx

"use client";

import { useEffect, useState } from "react";
import { ShieldCheck, Activity, AlertTriangle, Briefcase, Bell, RefreshCw } from "lucide-react";

// تم استخدام المسارات المباشرة والاسم الفعلي MetricsCard.tsx
import { dashboardService } from "../../lib/dashboardService";
import { DashboardSummary } from "../../types/dashboard";
import MetricCard from "../../components/dashboard/MetricCard";
import ExposureChart from "../../components/dashboard/ExposureChart";

export default function ExecutiveDashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchDashboardData = async (silent = false) => {
    if (!silent) setLoading(true);
    setIsRefreshing(true);
    setError(null);
    try {
      const data = await dashboardService.getSummary();
      setSummary(data);
      setLastRefreshed(new Date());
    } catch (err: any) {
      setError(`Failed to fetch live telemetry: ${err.message || "Unknown error"}`);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(() => {
      fetchDashboardData(true);
    }, 60000); // Auto-refresh every 60 seconds
    return () => clearInterval(interval);
  }, []);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value);
  };

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

  return (
    <div className="max-w-7xl mx-auto animate-in fade-in duration-500 space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Executive Dashboard</h1>
          <p className="text-sm text-slate-400 mt-1">Live enterprise compliance and risk telemetry.</p>
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-500">
          <span>Last sync: {lastRefreshed.toLocaleTimeString()}</span>
          <button 
            onClick={() => fetchDashboardData(false)}
            disabled={isRefreshing}
            className="p-2 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 hover:text-white transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricCard 
              title="Total Exposure" 
              value={formatCurrency(summary.total_exposure)} 
              change={summary.exposure_change} 
              icon={<Activity className="w-5 h-5" />} 
              isNegativeGood={true}
            />
            <MetricCard 
              title="Compliance Score" 
              value={summary.compliance_score} 
              change={summary.compliance_change} 
              icon={<ShieldCheck className="w-5 h-5" />} 
              suffix="%"
            />
            <MetricCard 
              title="Active Projects" 
              value={summary.active_projects} 
              icon={<Briefcase className="w-5 h-5" />} 
            />
            <MetricCard 
              title="Critical Risks" 
              value={summary.critical_risks} 
              icon={<AlertTriangle className="w-5 h-5" />} 
              isNegativeGood={true}
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 bg-slate-900/40 border border-slate-800 rounded-xl p-5">
              <h3 className="text-sm font-semibold text-slate-200 mb-1">Exposure Trends</h3>
              <p className="text-xs text-slate-500 mb-4">Financial risk exposure over the last 30 days.</p>
              {summary.exposure_trends && summary.exposure_trends.length > 0 ? (
                <ExposureChart data={summary.exposure_trends} />
              ) : (
                <div className="h-[300px] flex items-center justify-center text-slate-500 text-sm font-mono border border-dashed border-slate-800 rounded-lg mt-4">
                  No trend data available
                </div>
              )}
            </div>

            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-5 flex flex-col">
              <div className="flex items-center gap-2 mb-4">
                <Bell className="w-4 h-4 text-orange-400" />
                <h3 className="text-sm font-semibold text-slate-200">Executive Alerts</h3>
              </div>
              <div className="flex-1 overflow-y-auto pr-2 space-y-3 custom-scrollbar">
                {summary.alerts && summary.alerts.length > 0 ? (
                  summary.alerts.map((alert) => (
                    <div key={alert.id} className="p-3 bg-slate-950/50 border border-slate-800/80 rounded-lg border-l-2 border-l-red-500">
                      <div className="flex justify-between items-start mb-1">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-red-400">{alert.severity}</span>
                        <span className="text-[10px] text-slate-500 font-mono">{new Date(alert.timestamp).toLocaleDateString()}</span>
                      </div>
                      <p className="text-xs text-slate-300 leading-relaxed">{alert.message}</p>
                    </div>
                  ))
                ) : (
                  <div className="flex flex-col items-center justify-center h-full text-slate-500 opacity-50">
                    <ShieldCheck className="w-8 h-8 mb-2" />
                    <span className="text-xs">No active alerts</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}