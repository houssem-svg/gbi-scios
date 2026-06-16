import Sidebar from "@/components/layout/Sidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-300 font-sans selection:bg-blue-500/30">
      <Sidebar />
      <div className="md:ml-64 min-h-screen flex flex-col">
        <header className="h-16 border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-10 flex items-center px-8 justify-between">
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-4 bg-blue-600 rounded-full" />
            <h2 className="text-sm font-medium text-slate-200">Executive Dashboard</h2>
          </div>
          <div className="text-xs text-slate-500 font-mono">
            SYS.TIME: {new Date().toISOString().split('T')[0]}
          </div>
        </header>
        <main className="flex-1 p-8">
          {children}
        </main>
      </div>
    </div>
  );
}