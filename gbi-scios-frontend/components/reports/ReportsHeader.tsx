// src/components/reports/ReportsHeader.tsx

import { FileBarChart, ShieldAlert, TrendingDown } from "lucide-react";

export default function ReportsHeader() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 relative overflow-hidden">
        <div className="flex justify-between items-start">
          <div>
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Generated Reports</p>
            <h3 className="text-2xl font-semibold mt-1 text-slate-100">124</h3>
          </div>
          <div className="p-2 bg-blue-900/30 rounded-lg text-blue-400">
            <FileBarChart className="w-5 h-5" />
          </div>
        </div>
        <p className="text-xs text-slate-500 mt-4"><span className="text-emerald-400 font-medium">+12</span> this month</p>
      </div>

      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 relative overflow-hidden">
        <div className="flex justify-between items-start">
          <div>
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Exposure Tracked</p>
            <h3 className="text-2xl font-semibold mt-1 text-slate-100">8.4M SAR</h3>
          </div>
          <div className="p-2 bg-orange-900/30 rounded-lg text-orange-400">
            <TrendingDown className="w-5 h-5" />
          </div>
        </div>
        <p className="text-xs text-slate-500 mt-4"><span className="text-orange-400 font-medium">+1.2M SAR</span> since last scan</p>
      </div>

      <div className="bg-red-950/20 border border-red-900/50 rounded-xl p-5 relative overflow-hidden">
        <div className="flex justify-between items-start">
          <div>
            <p className="text-xs font-medium text-red-400/80 uppercase tracking-wider">Critical Waivers</p>
            <h3 className="text-2xl font-semibold mt-1 text-red-400">3</h3>
          </div>
          <div className="p-2 bg-red-900/30 rounded-lg text-red-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
        </div>
        <p className="text-xs text-slate-500 mt-4"><span className="text-red-400 font-medium">Action Required</span> immediately</p>
      </div>
    </div>
  );
}