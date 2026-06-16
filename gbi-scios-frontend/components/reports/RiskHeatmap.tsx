// src/components/reports/RiskHeatmap.tsx

export default function RiskHeatmap() {
  const zones = [
    { name: "Structural", risk: "high" },
    { name: "Electrical", risk: "medium" },
    { name: "Plumbing", risk: "low" },
    { name: "Finishing", risk: "critical" },
    { name: "HVAC", risk: "low" },
    { name: "Landscaping", risk: "low" },
    { name: "IT & Security", risk: "medium" },
    { name: "Facade", risk: "high" },
  ];

  const getColor = (risk: string) => {
    switch (risk) {
      case "critical": return "bg-red-500/80 border-red-500";
      case "high": return "bg-orange-500/80 border-orange-500";
      case "medium": return "bg-yellow-500/80 border-yellow-500";
      case "low": return "bg-emerald-500/80 border-emerald-500";
      default: return "bg-slate-800 border-slate-700";
    }
  };

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 mb-6 shadow-xl">
      <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider mb-4">Enterprise Risk Heatmap</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {zones.map((zone, index) => (
          <div key={index} className={`p-3 rounded-lg border flex flex-col justify-between h-24 ${getColor(zone.risk)}`}>
            <span className="text-xs font-semibold text-slate-950 uppercase tracking-wider">{zone.name}</span>
            <span className="text-[10px] font-bold text-slate-900 bg-white/30 self-start px-2 py-0.5 rounded-sm uppercase">
              {zone.risk}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}