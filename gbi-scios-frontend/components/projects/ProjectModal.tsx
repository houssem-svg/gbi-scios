"use client";

import { useForm } from "react-hook-form";
import { useEffect } from "react";
import { X, Loader2 } from "lucide-react";
import {
  Project,
  ProjectCreateInput,
  ProjectUpdateInput,
  ProjectStatus,
} from "@/types/project";

interface ProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ProjectCreateInput | ProjectUpdateInput) => Promise<void>;
  project?: Project | null;
}

type ProjectFormValues = {
  project_name: string;
  client_name: string;
  sector: string;
  status: ProjectStatus;
};

const STATUS_OPTIONS: ProjectStatus[] = [
  "Planning",
  "Active",
  "On Hold",
  "Completed",
  "Cancelled",
];

export default function ProjectModal({ isOpen, onClose, onSubmit, project }: ProjectModalProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ProjectFormValues>({
    defaultValues: {
      project_name: "",
      client_name: "",
      sector: "",
      status: "Planning",
    },
  });

  useEffect(() => {
    if (project) {
      reset({
        project_name: project.name || "",
        client_name: project.client || "",
        sector: project.sector || "",
        status: project.status || "Planning",
      });
    } else {
      reset({
        project_name: "",
        client_name: "",
        sector: "",
        status: "Planning",
      });
    }
  }, [project, reset, isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl shadow-2xl overflow-hidden relative">
        <div className="absolute top-0 left-0 w-full h-1 bg-blue-600" />
        <div className="flex justify-between items-center px-6 py-4 border-b border-slate-800/60">
          <h3 className="text-base font-semibold text-slate-100">
            {project ? "Edit Project" : "Create Project"}
          </h3>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 transition-colors"
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-1.5">
              Project Name
            </label>
            <input
              type="text"
              {...register("project_name", { required: "Project name is required" })}
              className="block w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
              placeholder="Strategic Project Name"
            />
            {errors.project_name && (
              <p className="mt-1 text-xs text-red-400">{errors.project_name.message}</p>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-1.5">
              Client Name
            </label>
            <input
              type="text"
              {...register("client_name", { required: "Client name is required" })}
              className="block w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
              placeholder="Authority / Entity Name"
            />
            {errors.client_name && (
              <p className="mt-1 text-xs text-red-400">{errors.client_name.message}</p>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-1.5">
              Sector
            </label>
            <input
              type="text"
              {...register("sector", { required: "Sector is required" })}
              className="block w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
              placeholder="e.g. Construction, Energy, IT"
            />
            {errors.sector && (
              <p className="mt-1 text-xs text-red-400">{errors.sector.message}</p>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-1.5">
              Status
            </label>
            <select
              {...register("status")}
              className="block w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
            >
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800/60 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 bg-slate-800/40 hover:bg-slate-800 border border-slate-800 rounded-lg transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex items-center gap-2 px-4 py-2 text-xs font-medium text-white bg-blue-600 hover:bg-blue-500 rounded-lg transition-all disabled:opacity-50 shadow-lg shadow-blue-900/20"
            >
              {isSubmitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              {project ? "Save Changes" : "Create Project"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
