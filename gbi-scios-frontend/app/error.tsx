"use client";

import { useEffect } from "react";
import { ShieldAlert, RotateCcw } from "lucide-react";

interface ErrorBoundaryProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function GlobalError({ error, reset }: ErrorBoundaryProps) {
  useEffect(() => {
    // Surface runtime errors to the browser console for debugging.
    console.error("GBI-SCIOS runtime error:", error);
  }, [error]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center px-6 text-center selection:bg-blue-500/30">
      <div className="w-14 h-14 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-center mb-5 shadow-lg">
        <ShieldAlert className="w-7 h-7 text-red-400" />
      </div>
      <h1 className="text-3xl font-bold tracking-widest">
        GBI<span className="text-blue-600">-SCIOS</span>
      </h1>
      <p className="text-xs text-slate-500 mt-2 uppercase tracking-[0.2em] font-medium">
        Unexpected Error
      </p>
      <p className="mt-4 text-sm text-slate-400 max-w-md">
        Something went wrong while rendering this page. You can try again, or
        return to the dashboard.
      </p>
      {error?.message && (
        <pre className="mt-4 max-w-xl overflow-x-auto rounded-lg border border-slate-800 bg-slate-900/60 px-4 py-3 text-xs font-mono text-red-400">
          {error.message}
        </pre>
      )}
      <div className="mt-6 flex items-center gap-3">
        <button
          onClick={reset}
          className="inline-flex items-center justify-center gap-2 px-5 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
          Try again
        </button>
        <a
          href="/dashboard"
          className="inline-flex items-center justify-center px-5 py-2 text-sm font-medium text-slate-300 bg-slate-900 border border-slate-800 hover:bg-slate-800 rounded-lg transition-colors"
        >
          Return to Dashboard
        </a>
      </div>
    </div>
  );
}
