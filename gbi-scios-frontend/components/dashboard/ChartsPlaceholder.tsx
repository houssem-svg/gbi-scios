export default function ChartsPlaceholder() {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-5 h-[300px] flex flex-col">
      <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider mb-4">Financial Exposure Trend</h3>
      <div className="flex-1 border border-dashed border-slate-700 rounded-md flex items-end p-4 gap-2 relative">
        <div className="absolute inset-0 flex flex-col justify-between p-4 pointer-events-none">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="w-full h-px bg-slate-800/50" />
          ))}
        </div>
        {[40, 70, 45, 90, 65, 80, 55, 95].map((height, i) => (
          <div
            key={i}
            className={`flex-1 rounded-t-sm opacity-80 transition-all hover:opacity-100 ${
              height > 85 ? 'bg-red-500/50' : 'bg-blue-600/50'
            }`}
            style={{ height: `${height}%` }}
          />
        ))}
      </div>
    </div>
  );
}