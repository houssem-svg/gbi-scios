import { AlertTriangle, AlertCircle } from "lucide-react";

export default function AlertsPanel() {
  const alerts = [
    {
      id: 1,
      project: "GBI-SCIOS Alpha",
      issue: "Budget Exposure Exceeds 90%",
      severity: "critical",
      time: "2 hours ago"
    },
    {
      id: 2,
      project: "Riyadh Metro Extension",
      issue: "Mandatory List Violations Detected",
      severity: "high",
      time: "5 hours ago"
    }
  ];

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">Executive Alerts</h3>
        <span className="bg-red-900/30 text-red-400 text-xs px-2 py-1 rounded-full font-medium border border-red-900/50">
          2 Action Required
        </span>
      </div>
      <div className="space-y-3">
        {alerts.map((alert) => (
          <div key={alert.id} className="p-3 bg-slate-950 border border-slate-800 rounded-md flex gap-3">
            <div className="mt-0.5">
              {alert.severity === 'critical' ? (
                <AlertTriangle className="w-4 h-4 text-red-500" />
              ) : (
                <AlertCircle className="w-4 h-4 text-orange-500" />
              )}
            </div>
            <div>
              <p className="text-sm font-medium text-slate-200">{alert.project}</p>
              <p className="text-xs text-slate-400 mt-1">{alert.issue}</p>
              <p className="text-xs text-slate-600 mt-2">{alert.time}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}