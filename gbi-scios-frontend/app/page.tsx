"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Shield, Loader2 } from "lucide-react";

export default function Home() {
  const router = useRouter();
  const [deciding, setDeciding] = useState(true);

  useEffect(() => {
    // Read the access_token cookie presence to decide where to send the user.
    const hasToken =
      typeof document !== "undefined" &&
      document.cookie.split(";").some((c) => c.trim().startsWith("access_token="));
    router.replace(hasToken ? "/dashboard" : "/login");
    // Give the router a tick; the spinner below stays visible meanwhile.
    const t = setTimeout(() => setDeciding(false), 1500);
    return () => clearTimeout(t);
  }, [router]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center px-6 selection:bg-blue-500/30">
      <div className="absolute top-0 left-0 w-full h-1 bg-blue-600" />
      <div className="flex flex-col items-center text-center">
        <div className="w-14 h-14 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-center mb-5 shadow-lg">
          <Shield className="w-7 h-7 text-blue-500" />
        </div>
        <h1 className="text-3xl font-bold tracking-widest">
          GBI<span className="text-blue-600">-SCIOS</span>
        </h1>
        <p className="text-xs text-slate-500 mt-3 uppercase tracking-[0.2em] font-medium">
          Sovereign Compliance Intelligence Platform
        </p>
        <div className="mt-8 flex items-center gap-2 text-sm text-slate-400">
          {deciding ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Redirecting…</span>
            </>
          ) : (
            <span>Routing you to your workspace.</span>
          )}
        </div>
      </div>
      <footer className="absolute bottom-6 text-[10px] text-slate-700 uppercase tracking-wider">
        &copy; {new Date().getFullYear()} GBI-SCIOS. All rights reserved.
      </footer>
    </div>
  );
}
