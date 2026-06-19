// src/components/dashboard/ExposureChart.tsx

"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { TopRiskProject } from "@/types/dashboard";

interface ExposureChartProps {
  data: TopRiskProject[];
}

const formatCurrency = (value: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value || 0);

export default function ExposureChart({ data }: ExposureChartProps) {
  const chartData = data.map((p) => ({
    name: p.project_name ?? p.project_id,
    exposure: p.project_exposure ?? 0,
    flags: p.flag_count ?? 0,
  }));

  if (chartData.length === 0) {
    return (
      <div className="h-[300px] flex items-center justify-center text-slate-500 text-sm font-mono border border-dashed border-slate-800 rounded-lg mt-4">
        No risk exposure data available
      </div>
    );
  }

  return (
    <div className="h-[300px] w-full mt-4">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis
            dataKey="name"
            stroke="#64748b"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value: string) =>
              value && value.length > 14 ? `${value.slice(0, 13)}…` : value
            }
          />
          <YAxis
            stroke="#64748b"
            fontSize={12}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value: number) => formatCurrency(value)}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#0f172a",
              borderColor: "#1e293b",
              borderRadius: "0.5rem",
              fontSize: "12px",
            }}
            itemStyle={{ color: "#e2e8f0" }}
            formatter={(value: number) => [formatCurrency(value), "Exposure"]}
          />
          <Bar dataKey="exposure" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, idx) => (
              <Cell
                key={`cell-${idx}`}
                fill={entry.exposure > 1_000_000 ? "#ef4444" : entry.exposure > 100_000 ? "#f97316" : "#22c55e"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
