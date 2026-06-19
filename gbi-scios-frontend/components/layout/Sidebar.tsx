"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LayoutDashboard, FolderKanban, FileText, LogOut, Scale } from "lucide-react";
import { useAuth } from "@/components/providers/AuthProvider";

interface NavItem {
  name: string;
  icon: typeof LayoutDashboard;
  href: string;
}

const NAV_ITEMS: NavItem[] = [
  { name: "Executive Summary", icon: LayoutDashboard, href: "/dashboard" },
  { name: "Projects Workspace", icon: FolderKanban, href: "/dashboard/projects" },
  { name: "Bid Evaluation", icon: Scale, href: "/dashboard/evaluations" },
  { name: "Sovereign Reports", icon: FileText, href: "/dashboard/reports" },
  { name: "Upload Center", icon: LayoutDashboard, href: "/dashboard/uploads" },
];

function getInitials(name?: string | null): string {
  if (!name) return "U";
  const parts = name.trim().split(/\s+/).slice(0, 2);
  if (parts.length === 0) return "U";
  return parts.map((p) => p[0]?.toUpperCase() ?? "").join("") || "U";
}

function formatRole(role?: string): string {
  if (!role) return "User";
  // Pretty-print e.g. "admin" → "Admin", "executive" → "Executive"
  return role.charAt(0).toUpperCase() + role.slice(1).toLowerCase();
}

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    // AuthProvider.logout already pushes to /login; this is a safety net.
    router.push("/login");
  };

  const isActive = (href: string): boolean =>
    href === "/dashboard" ? pathname === "/dashboard" : pathname.startsWith(href);

  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800 hidden md:flex flex-col h-screen fixed">
      <div className="p-6">
        <h1 className="text-xl font-bold tracking-widest text-slate-100">
          GBI<span className="text-blue-600">-SCIOS</span>
        </h1>
        <p className="text-xs text-slate-500 mt-1 uppercase tracking-wider">Enterprise Console</p>
      </div>
      <nav className="flex-1 px-4 space-y-1 mt-4">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.href);
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
                active
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
            {getInitials(user?.full_name)}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-slate-200 truncate">
              {user?.full_name || user?.email || "Unknown User"}
            </p>
            <p className="text-xs text-slate-500 truncate">{formatRole(user?.role)}</p>
          </div>
          <button
            onClick={handleLogout}
            title="Sign out"
            aria-label="Sign out"
            className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-md transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
