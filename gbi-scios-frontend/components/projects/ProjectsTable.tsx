"use client";

import { useState } from "react";
import { Edit2, Trash2, Folder, ShieldX, UploadCloud, Loader2 } from "lucide-react";
import { Project, ProjectStatus } from "@/types/project";

interface ProjectsTableProps {
  projects: Project[];
  loading: boolean;
  onEditClick: (project: Project) => void;
  onDeleteClick: (project: Project) => void;
}

const STATUS_COLORS: Record<ProjectStatus, string> = {
  Planning: "bg-slate-700 text-slate-200",
  Active: "bg-emerald-900/50 text-emerald-300",
  "On Hold": "bg-amber-900/50 text-amber-300",
  Completed: "bg-blue-900/50 text-blue-300",
  Cancelled: "bg-red-900/50 text-red-300",
};

export default function ProjectsTable({ projects, loading, onEditClick, onDeleteClick }: ProjectsTableProps) {
  const [uploadingProjectId, setUploadingProjectId] = useState<string | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>, projectId: string) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith(".csv")) {
      alert("Invalid file format. Please upload a standard CSV dataset.");
      return;
    }

    setUploadingProjectId(projectId);
    try {
      const formData = new FormData();
      formData.append("project_id", String(projectId).trim());
      formData.append("file", file, file.name);

      const { apiClient } = await import("@/lib/api");
      await apiClient.request("/uploads", {
        method: "POST",
        body: formData,
      });

      alert("CSV uploaded successfully.");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Upload failed.";
      alert(msg);
    } finally {
      setUploadingProjectId(null);
      if (e.target) {
        (e.target as HTMLInputElement).value = "";
      }
    }
  };

  if (loading) {
    return (
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden space-y-4 p-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="flex items-center justify-between animate-pulse">
            <div className="space-y-2 w-1/3">
              <div className="h-4 bg-slate-800 rounded w-3/4"></div>
              <div className="h-3 bg-slate-800 rounded w-1/2"></div>
            </div>
            <div className="h-4 bg-slate-800 rounded w-1/4"></div>
            <div className="h-4 bg-slate-800 rounded w-12"></div>
          </div>
        ))}
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-16 bg-slate-900/30 border border-slate-800 border-dashed rounded-xl text-center">
        <div className="p-3 bg-slate-900 rounded-xl border border-slate-800 mb-4 text-slate-500">
          <ShieldX className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-medium text-slate-300">No projects yet</h3>
        <p className="text-xs text-slate-500 max-w-xs mt-1">
          Create your first project to start tracking compliance.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm whitespace-nowrap">
          <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800">
            <tr>
              <th className="px-6 py-4 font-medium uppercase tracking-wider text-xs">Project</th>
              <th className="px-6 py-4 font-medium uppercase tracking-wider text-xs">Client</th>
              <th className="px-6 py-4 font-medium uppercase tracking-wider text-xs">Sector</th>
              <th className="px-6 py-4 font-medium uppercase tracking-wider text-xs">Status</th>
              <th className="px-6 py-4 font-medium text-right uppercase tracking-wider text-xs">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {projects.map((project) => (
              <tr key={project.id} className="hover:bg-slate-800/30 transition-colors group">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <Folder className="w-4 h-4 text-blue-500/70" />
                    <div>
                      <div className="font-medium text-slate-200">{project.name}</div>
                      <div className="text-xs text-slate-500 mt-0.5 font-mono">{project.id}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 text-slate-300">{project.client}</td>
                <td className="px-6 py-4 text-slate-300">{project.sector || "—"}</td>
                <td className="px-6 py-4">
                  <span
                    className={`px-2.5 py-0.5 rounded-md text-xs font-medium ${STATUS_COLORS[project.status]}`}
                  >
                    {project.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-right">
                  <input
                    type="file"
                    id={`csv-file-${project.id}`}
                    className="hidden"
                    accept=".csv"
                    onChange={(e) => handleFileChange(e, project.id)}
                  />

                  <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    {uploadingProjectId === project.id ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-400 mr-1" />
                    ) : (
                      <label
                        htmlFor={`csv-file-${project.id}`}
                        className="p-1 text-slate-400 hover:text-emerald-400 rounded hover:bg-slate-800 transition-colors cursor-pointer block"
                        title="Upload CSV"
                      >
                        <UploadCloud className="w-3.5 h-3.5" />
                      </label>
                    )}

                    <button
                      onClick={() => onEditClick(project)}
                      className="p-1 text-slate-400 hover:text-blue-400 rounded hover:bg-slate-800 transition-colors"
                      title="Edit"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => onDeleteClick(project)}
                      className="p-1 text-slate-400 hover:text-red-400 rounded hover:bg-slate-800 transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
