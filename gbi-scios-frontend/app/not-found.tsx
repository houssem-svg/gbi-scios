import Link from "next/link";
import { ShieldAlert } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center px-6 text-center selection:bg-blue-500/30">
      <div className="w-14 h-14 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-center mb-5 shadow-lg">
        <ShieldAlert className="w-7 h-7 text-amber-400" />
      </div>
      <h1 className="text-3xl font-bold tracking-widest">
        GBI<span className="text-blue-600">-SCIOS</span>
      </h1>
      <p className="text-xs text-slate-500 mt-2 uppercase tracking-[0.2em] font-medium">
        404 — Page Not Found
      </p>
      <p className="mt-4 text-sm text-slate-400 max-w-md">
        The page you are looking for does not exist or has been moved.
      </p>
      <Link
        href="/dashboard"
        className="mt-6 inline-flex items-center justify-center px-5 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors"
      >
        Return to Dashboard
      </Link>
    </div>
  );
}
