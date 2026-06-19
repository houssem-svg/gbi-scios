import { Shield, Loader2 } from "lucide-react";

export default function Loading() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center px-6 text-center selection:bg-blue-500/30">
      <div className="w-14 h-14 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-center mb-5 shadow-lg">
        <Shield className="w-7 h-7 text-blue-500" />
      </div>
      <h1 className="text-3xl font-bold tracking-widest">
        GBI<span className="text-blue-600">-SCIOS</span>
      </h1>
      <p className="text-xs text-slate-500 mt-2 uppercase tracking-[0.2em] font-medium">
        Sovereign Compliance Intelligence Platform
      </p>
      <div className="mt-6 flex items-center gap-2 text-sm text-slate-400">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span>Loading…</span>
      </div>
    </div>
  );
}
