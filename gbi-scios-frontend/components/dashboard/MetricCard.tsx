// components/dashboard/MetricsCard.tsx

"use client";

import { ReactNode } from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  icon: ReactNode;
  suffix?: string;
  isNegativeGood?: boolean;
}

export default function MetricCard({ title, value, change, icon, suffix = "", isNegativeGood = false }: MetricCardProps) {
  const isPositive = change !== undefined && change > 0;
  const isZero = change === 0 || change === undefined;
  
  let changeColor = "text-slate-500";
  if (!isZero) {
    if (isNegativeGood) {
      changeColor = isPositive ? "text-red-400" : "text-emerald-400";
    } else {
      changeColor = isPositive ? "text-emerald-400" : "text-red-400";
    }
  }

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 hover:bg-slate-800/40 transition-all duration-300">
      <div className="flex justify-between items-start mb-4">
        <div className="p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-blue-400">
          {icon}
        </div>
        {change !== undefined && (
          <div className={`flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-md bg-slate-950/50 border border-slate-800/50 ${changeColor}`}>
            {isPositive ? <TrendingUp className="w-3 h-3" /> : isZero ? <Minus className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
            {Math.abs(change)}%
          </div>
        )}
      </div>
      <div>
        <p className="text-xs text-slate-500 uppercase tracking-wider font-medium mb-1">{title}</p>
        <h4 className="text-3xl font-bold text-slate-100 font-mono tracking-tight">
          {value}{suffix}
        </h4>
      </div>
    </div>
  );
}