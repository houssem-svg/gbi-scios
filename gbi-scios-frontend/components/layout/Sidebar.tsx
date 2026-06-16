import Link from "next/link";
import { LayoutDashboard, ShieldAlert, FolderKanban, FileText, Settings } from "lucide-react";

export default function Sidebar() {
  const navItems = [
    { name: "Executive Summary", icon: LayoutDashboard, href: "/dashboard", active: true },
    { name: "Projects Workspace", icon: FolderKanban, href: "/dashboard/projects", active: false },
    { name: "Compliance Engine", icon: ShieldAlert, href: "/dashboard/compliance", active: false },
    { name: "Sovereign Reports", icon: FileText, href: "/dashboard/reports", active: false },
    { name: "System Settings", icon: Settings, href: "/dashboard/settings", active: false },
  ];

  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800 hidden md:flex flex-col h-screen fixed">
      <div className="p-6">
        <h1 className="text-xl font-bold tracking-widest text-slate-100">
          GBI<span className="text-blue-600">-SCIOS</span>
        </h1>
        <p className="text-xs text-slate-500 mt-1 uppercase tracking-wider">Enterprise Console</p>
      </div>
      <nav className="flex-1 px-4 space-y-1 mt-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
                item.active
                  ? "bg-blue-900/20 text-blue-400 border border-blue-900/50"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              <Icon className="w-4 h-4" />
              {item.name}
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-slate-800">
        <div className="flex items-center gap-3 px-3 py-2">
          <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold text-slate-300">
            AD
          </div>
          <div>
            <p className="text-sm font-medium text-slate-200">Admin User</p>
            <p className="text-xs text-slate-500">Director Level</p>
          </div>
        </div>
      </div>
    </aside>
  );
}