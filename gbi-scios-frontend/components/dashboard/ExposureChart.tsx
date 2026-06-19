// src/components/dashboard/ExposureChart.tsx

"use client";

import dynamic from "next/dynamic";
import type { TopRiskProject } from "@/types/dashboard";

/**
 * recharts pulls in a large DOM-heavy dependency tree. Per audit item
 * C-2/C-5/C-11 we load the whole chart component lazily via next/dynamic
 * with ssr:false so recharts only ships in the client bundle (no SSR cost,
 * no hydration warnings from recharts' ResponsiveContainer).
 *
 * Previously each recharts sub-component was dynamically imported individually,
 * which produced TS errors because next/dynamic's type inference doesn't play
 * well with recharts' class-component defaultProps. Loading one wrapper
 * component that statically imports recharts avoids that entirely.
 */
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

function ExposureChartInner({ data }: ExposureChartProps) {
  // Lazy-load recharts only inside the client wrapper to keep its types intact.
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Cell,
  } = require("recharts") as typeof import("recharts");

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
                fill={
                  entry.exposure > 1_000_000
                    ? "#ef4444"
                    : entry.exposure > 100_000
                      ? "#f97316"
                      : "#22c55e"
                }
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Default export is a dynamically-loaded wrapper around the inner chart.
 * ssr:false ensures recharts (which depends on the DOM) never runs on the server.
 */
export default dynamic(() => Promise.resolve(ExposureChartInner), {
  ssr: false,
  loading: () => (
    <div className="h-[300px] flex items-center justify-center text-slate-500 text-sm font-mono border border-dashed border-slate-800 rounded-lg mt-4">
      Loading chart…
    </div>
  ),
});
